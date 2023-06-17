from flask import Flask, render_template, request, url_for, redirect, flash, app
from flask_login import LoginManager, login_required, UserMixin, login_user, logout_user, current_user
from datetime import timedelta
import Database.DBMS_Movie as DBMS_Movie
import Database.User as DBUser
import configparser

login_manager = LoginManager()
app = Flask(__name__)
DBMS_Movie = DBMS_Movie.DBMS_Movie()
dbUser = DBUser.Database()
login_manager.init_app(app)
config = configparser.ConfigParser()
config.read('../Config/config.ini')
app.config.update(TESTING=True, SECRET_KEY='192b9bdd22ab9ed4d12e236c78afcb9a393ec15f71bbf5dc987d54727823bcbf')


class User(UserMixin):
    def __init__(self, id):
        user_data = dbUser.get_user_by_id(id)
        print(user_data)
        self.id = user_data[0]
        self.username = user_data[1]
        self.password = user_data[2]
        self.name = user_data[3]
        self.email = user_data[4]
        self.dob = user_data[5]


@login_manager.user_loader
def load_user(user_id):
    # Retrieve the user from the database using the provided user_id
    user_data = dbUser.get_user_by_id(user_id)
    if user_data:
        id, username, password, profilename, email, dob = user_data
        return User(id)

    return None


# Site Landing Page
@app.route('/', methods=['GET', 'POST'])
def login_page():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        # Check if username and password are correct
        db_password = dbUser.get_password_by_username(username)
        if db_password:
            if password == db_password[1]:
                print("Matched, logging in...")
                user = User(dbUser.get_user_by_id(db_password[0])[0])
                login_user(user, remember=True, duration=timedelta(minutes=5))
                return redirect(url_for('home'))
            else:
                print('Username or Password is incorrect')
                error = 'Username or Password is incorrect'
        else:
            print('Username or Password is incorrect')
            error = 'Username or Password is incorrect'
            return redirect(url_for('login_page'))
    return render_template('login.html', error=error)


# Site Landing Page
@app.route('/sign-up', methods=['GET', 'POST'])
def signup_page():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        profilename = request.form['profilename']
        email = request.form['email']
        dob = request.form['dob']
        # Check if username and password are correct
        check = dbUser.check_username_exists(username)
        if check:
            print('Username already exists')
            error = 'Username already exists'
        else:
            dbUser.create_user(username, password, profilename, email, dob)
            print('Account Created')
            return redirect(url_for('login_page'))
    return render_template('signup.html', error=error)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login_page'))


@app.route('/home', methods=['GET'])
def home():
    page = 1
    limit = int(config.get("MOVIE", "LIMIT"))
    movie_list = DBMS_Movie.Movie_list(page=page, limit=limit)
    pages = DBMS_Movie.get_pages(pages=page, limit=limit)
    pages_left = pages["pages_left"]
    total_pages = pages["total_pages"]
    carousel = DBMS_Movie.carousel()

    return render_template(
        'index.html',
        movie_list=movie_list,
        total_pages=total_pages,
        pages_left=pages_left,
        carousel=carousel,
        page=page
    )


@app.route('/home/page/<int:page>', methods=['GET'])
def home_page(page):
    limit = int(config.get("MOVIE", "LIMIT"))
    pages = DBMS_Movie.get_pages(pages=page, limit=limit)
    pages_left = pages["pages_left"]
    total_pages = pages["total_pages"]

    # TODO: Convert to error page
    if page < 1:
        raise Exception('Page not found')
    elif page > total_pages:
        raise Exception('Page not found')

    movie_list = DBMS_Movie.Movie_list(page=page, limit=limit)
    carousel = DBMS_Movie.carousel()

    # Reload Movies block in index.html
    return render_template(
        'index.html',
        movie_list=movie_list,
        total_pages=total_pages,
        pages_left=pages_left,
        carousel=carousel,
        page=page
    )


@app.route('/movie/<string:movie_name>', methods=['GET'])
def movie_page(movie_name: str = None) -> str:
    """
    Get all movie details and render movie page
    :param movie_name: Movie name
    :return: Render movie page
    """
    # Remove (year) from movie name
    movie_name = movie_name.split('(')[0]
    movie = DBMS_Movie.get_movie_by_title(movie_name)

    movie_details = movie['movie']
    movie_genres = movie['genres']
    movie_director = movie['director']
    movie_actors = movie['actors']

    return render_template(
        'Movie/Movie_details.html',
        movie=movie_details,
        genres=movie_genres,
        director=movie_director,
        actors=movie_actors
    )


@app.route('/actor/<string:actor_name>', methods=['GET'])
@app.route('/actor/<int:tmdb_id>', methods=['GET'])
def actor(actor_name: str = None, tmdb_id: int = None) -> str:
    """
    Get all actor details and render actor page. Either actor_name or tmdb_id must be provided

    :param order:
    :param order_by:
    :param actor_name: Actor's name
    :param tmdb_id: Actor's TMDB ID
    :return:
    """
    if not actor_name and not tmdb_id:
        raise Exception('Actor name or TMDB ID must be provided')

    actor_details = DBMS_Movie.Actor(
        actor_name=actor_name if actor_name else None,
        actor_tmdb_id=tmdb_id if tmdb_id else None,
    )

    if not actor_details:
        # TODO: Convert to error page
        raise Exception('Actor not found')

    movie_list = actor_details['movies']

    actor_details = actor_details['actor']
    actor_name = actor_details['name']
    actor_aka = actor_details['also_known_as']
    actor_bio = actor_details['biography']
    actor_birthday = actor_details['birthday']
    actor_deathday = actor_details['deathday']
    actor_tmdb_page = config.get('MOVIE', 'TMDB_PERSON_URL') + str(actor_details['id'])
    actor_profile_path = config.get('MOVIE', 'TMDB_IMAGE_URL') + actor_details['profile_path'] if \
        actor_details['profile_path'] else None

    return render_template(
        'Actor/Actor.html',
        actor_name=actor_name,
        actor_aka=actor_aka,
        actor_bio=actor_bio,
        actor_birthday=actor_birthday,
        actor_deathday=actor_deathday,
        actor_profile_path=actor_profile_path,
        actor_tmdb_page=actor_tmdb_page,
        movie_list=movie_list
    )


@app.route('/director/<string:director_name>', methods=['GET'])
@app.route('/director/<int:tmdb_id>', methods=['GET'])
def director_page(director_name: str = None, tmdb_id: int = None) -> str:
    """
    Get all director details and render director page. Either director_name or tmdb_id must be provided

    :param director_name: Director's name
    :param tmdb_id: tmdb id of director
    :return: Render director page
    """
    if not director_name and not tmdb_id:
        raise Exception('Director name or TMDB ID must be provided')

    director_details = DBMS_Movie.Director(
        director_name=director_name if director_name else None,
        director_tmdb_id=tmdb_id if tmdb_id else None,
    )

    if not director_details:
        raise Exception('Director not found')

    movie_list = director_details['movies']

    director_details = director_details['director']

    director_name = director_details['name']
    director_aka = director_details['also_known_as'] or None
    director_bio = director_details['biography'] or None
    director_birthday = director_details['birthday'] or None
    director_deathday = director_details['deathday'] or None
    director_tmdb_page = config.get('MOVIE', 'TMDB_PERSON_URL') + str(director_details['id'])
    director_profile_path = config.get('MOVIE', 'TMDB_IMAGE_URL') + director_details['profile_path'] if \
        director_details['profile_path'] else None

    return render_template(
        'Director/Director.html',
        movie_list=movie_list,
        director_name=director_name,
        director_aka=director_aka,
        director_bio=director_bio,
        director_birthday=director_birthday,
        director_deathday=director_deathday,
        director_profile_path=director_profile_path,
        director_tmdb_page=director_tmdb_page
    )


# search
@app.route('/search', methods=['POST'])
def search():
    choice = request.form['choice']
    query = request.form['search']
    if choice == 'director':
        # search for directors
        results = DBMS_Movie.search_directors(query)
        print(results)
    elif choice == 'actor':
        # search for actors
        results = DBMS_Movie.search_actors(query)
    elif choice == 'movie':
        # search for movie
        results = DBMS_Movie.search_movies(query)
    else:
        # Handle invalid choice
        results = []
    return render_template('search.html', results=results, choice=choice)


# Error Site Route
# # Error handling page for not found sites / locations
# @app.errorhandler(404)
# def page_not_found(e):
#     return render_template('404.html'), 404

# Profile Page
@app.route('/profile', methods=['GET'])
def profile():
    # Get user's username
    print(current_user.id)

    userData = User(dbUser.get_user_by_id(current_user.id)[0])

    return render_template(
        'profile.html',
        userData=userData,
    )


if __name__ == '__main__':
    app.run(
        host=config.get('FLASK', 'HOST'),
        port=int(config.get('FLASK', 'PORT')),
        debug=bool(config.get('FLASK', 'DEBUG'))
    )
