from flask import Flask, render_template, request, url_for, redirect, flash, app
from flask_login import LoginManager, login_required, UserMixin, login_user, logout_user, current_user
from datetime import timedelta

import Database.Mongo as Mongo
from routes import *
import Database.User as DBUser
from Config.ConfigManager import ConfigManager

login_manager = LoginManager()
app = Flask(__name__)
dbUser = DBUser.Database()
config_manager = ConfigManager()
config = config_manager.get_config()
login_manager.init_app(app)
app.config.update(TESTING=True, SECRET_KEY='192b9bdd22ab9ed4d12e236c78afcb9a393ec15f71bbf5dc987d54727823bcbf')
app.register_blueprint(routes)


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
        return redirect(url_for('routes.home'))
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
                return redirect(url_for('routes.home'))
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
        return redirect(url_for('routes.home'))
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
# # Error handling page for not found sites / locations
# @app.errorhandler(404)
# def page_not_found(e):
#     return render_template('404.html'), 404

# Profile Page
@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile(success=None):
    # Mongodb handler
    handler = Mongo.MongoDBHandler(config.get('MONGODB', 'CONNECTION_STRING'), config.get('MONGODB', 'DATABASE'))

    # Get user's username and data
    print(current_user.id)
    userData = User(dbUser.get_user_by_id(current_user.id)[0])
    # Update user's data
    print(success)
    if request.method == 'POST':
        username = request.form['username']
        password = userData.password
        profilename = request.form['profilename']
        email = request.form['email']
        dob = request.form['dob']
        dbUser.update_user(current_user.id, username, password, profilename, email, dob)
        success = 'Profile Updated'
        return redirect(url_for('profile', success=success))

    # Print our user follow list
    userFollows = handler.find_documents(config.get('MONGODB', 'FOLLOW_COLLECTION'), {'user_id': current_user.id})
    userFollowsName = []
    if userFollows:
        userFollows = userFollows[0]['following_arr']
        for user in userFollows:
            userFollowsName.append(dbUser.get_user_by_id(user))
    else:
        handler.insert_document(config.get('MONGODB', 'FOLLOW_COLLECTION'), {'user_id': current_user.id, 'following_arr': []})

    # Print Movie watch list
    movieWatchList = handler.find_documents(config.get('MONGODB', 'WATCHLIST_COLLECTION'), {'user_id': current_user.id})
    movieWatchListName = []
    if movieWatchList:
        movieWatchList = movieWatchList[0]['watchlist_arr']
        for movie in movieWatchList:
            movieWatchListName.append(DBMS_Movie.get_movie_by_id(movie)[1])

    print(movieWatchListName)
    return render_template(
        'profile.html',
        userData=userData,
        success=success,
        userFollows=userFollowsName,
        movieWatchListName=movieWatchListName
    )


# Other user profile page
@app.route('/profile/<id>', methods=['GET', 'POST'])
def other_profile(id):
    # Mongodb handler
    handler = Mongo.MongoDBHandler(config.get('MONGODB', 'CONNECTION_STRING'), config.get('MONGODB', 'DATABASE'))

    # Get user's username and data
    userData = dbUser.get_user_by_id(id)

    # Check if user is followed
    userFollows = handler.find_documents(config.get('MONGODB', 'FOLLOW_COLLECTION'), {'user_id': current_user.id})[0]['following_arr']
    if userFollows:
        if userData[0] in userFollows:
            followed = True
        else:
            followed = False
    else:
        handler.insert_document(config.get('MONGODB', 'FOLLOW_COLLECTION'), {'user_id': current_user.id, 'following_arr': []})
    # Default follow value
    followed = False

    # Print our user follow list
    userFollows = handler.find_documents('user_follows', {'user_id': userData[0]})
    userFollowsName = []
    if userFollows:
        userFollows = userFollows[0]['following_arr']
        for user in userFollows:
            userFollowsName.append(dbUser.get_user_by_id(user))

    # Print Movie watch list
    movieWatchList = handler.find_documents('watchlist', {'user_id': userData[0]})
    movieWatchListName = []
    if movieWatchList:
        movieWatchList = movieWatchList[0]['watchlist_arr']
        for movie in movieWatchList:
            movieWatchListName.append(DBMS_Movie.get_movie_by_id(movie)[1])

    # Functions that require user to be authenticated
    if current_user.is_authenticated:
        # Check if user is followed
        userFollows = handler.find_documents('user_follows', {'user_id': current_user.id})[0]['following_arr']
        if userFollows:
            if userData[0] in userFollows:
                followed = True
            else:
                followed = False
        else:
            handler.insert_document('user_follows', {'user_id': current_user.id, 'following_arr': []})

    # Follow user
    if request.method == 'POST':
        print("Is user followed: " + str(followed))
        if not followed:
            handler.update_document(config.get('MONGODB', 'FOLLOW_COLLECTION'), {'user_id': current_user.id}, {'following_arr': userData[0]},
                                    '$push')
        else:
            handler.update_document(config.get('MONGODB', 'FOLLOW_COLLECTION'), {'user_id': current_user.id}, {'following_arr': userData[0]},
                                    '$pull')
        return redirect(url_for('other_profile', id=id))
        # Follow user
        if request.method == 'POST':
            print("Is user followed: " + str(followed))
            if not followed:
                handler.update_document('user_follows', {'user_id': current_user.id}, {'following_arr': userData[0]},
                                        '$push')
            else:
                handler.update_document('user_follows', {'user_id': current_user.id}, {'following_arr': userData[0]},
                                        '$pull')
            return redirect(url_for('other_profile', id=id))

    # Print our user follow list
    userFollows = handler.find_documents(config.get('MONGODB', 'FOLLOW_COLLECTION'), {'user_id': userData[0]})
    userFollowsName = []
    if userFollows:
        userFollows = userFollows[0]['following_arr']
        for user in userFollows:
            userFollowsName.append(dbUser.get_user_by_id(user))

    return render_template(
        'profile_view.html',
        userData=userData,
        followed=followed,
        userFollows=userFollowsName,
        movieWatchListName=movieWatchListName
    )


if __name__ == '__main__':
    app.run(
        host=config.get('FLASK', 'HOST'),
        port=int(config.get('FLASK', 'PORT')),
        debug=bool(config.get('FLASK', 'DEBUG'))
    )
