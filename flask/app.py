from flask import Flask, render_template, request, url_for, redirect, flash, app
from flask_login import LoginManager, login_required, UserMixin, login_user, logout_user, current_user
from datetime import timedelta
import Database.DBMS_Movie.DBMS_Movie as DBMS_Movie
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


# Error Site Route
@app.route('/home', methods=['GET'])
def home():
    page = 1
    limit = 12
    movie_list = DBMS_Movie.Movie_list(page=page, limit=limit)
    pages = DBMS_Movie.get_pages(pages=page, limit=12)
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
    pages = DBMS_Movie.get_pages(pages=page, limit=12)
    pages_left = pages["pages_left"]
    total_pages = pages["total_pages"]

    # TODO: Convert to error page
    if page < 1:
        raise Exception('Page not found')
    elif page > total_pages:
        raise Exception('Page not found')

    movie_list = DBMS_Movie.Movie_list(page=page, limit=12)
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
def movie_page(movie_name):
    # Remove (year) from movie name
    movie_name = movie_name.split('(')[0]
    movie = DBMS_Movie.get_movie_by_title(movie_name)
    movie_details = movie['movie']
    movie_genres = movie['genres']
    movie_director = movie['director']
    movie_actors = movie['actors']
    return render_template(
        'Movie_details.html',
        movie=movie_details,
        genres=movie_genres,
        director=movie_director,
        actors=movie_actors
    )


# # Error handling page for not found sites / locations
# @app.errorhandler(404)
# def page_not_found(e):
#     return render_template('404.html'), 404


if __name__ == '__main__':
    app.run(
        host=config.get('FLASK', 'HOST'),
        port=int(config.get('FLASK', 'PORT')),
        debug=bool(config.get('FLASK', 'DEBUG'))
    )
