import hashlib
from datetime import timedelta

from flask import render_template, request, redirect, url_for
from flask_login import UserMixin, current_user, login_user, logout_user

from . import routes
import Database.DBMS_Movie as DBMS_Movie
from Config.ConfigManager import ConfigManager
import Database.User as DBUser
from Database import Mongo

DBMS_Movie = DBMS_Movie
dbUser = DBUser.Database()
config_manager = ConfigManager()
config = config_manager.get_config()
handler = Mongo.MongoDBHandler.get_instance(
    config.get('MONGODB', 'CONNECTION_STRING'),
    config.get('MONGODB', 'DATABASE')
)


class User(UserMixin):
    def __init__(self, id):
        user_data = dbUser.get_user_by_id(id)
        self.id = user_data[0]
        self.username = user_data[1]
        self.password = user_data[2]
        self.name = user_data[3]
        self.email = user_data[4]
        self.dob = user_data[5]


# Site Landing Page
@routes.route('/login', methods=['GET', 'POST'])
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
            # hash input password
            hashedpassword = hashlib.sha512(password.encode('UTF-8')).hexdigest()
            print("Hashed:" + str(hashedpassword))
            print("DB:" + str(db_password[1]))
            if hashedpassword == db_password[1]:
                print("Matched, logging in...")
                user = User(dbUser.get_user_by_id(db_password[0])[0])
                login_user(user, remember=True, duration=timedelta(minutes=5))
                if current_user.username == 'admin':
                    return redirect(url_for('routes.admin'))
                else:
                    return redirect(url_for('routes.home'))
            else:
                print('Username or Password is incorrect')
                error = 'Username or Password is incorrect'
        else:
            print('Username or Password is incorrect')
            error = 'Username or Password is incorrect'
            return redirect(url_for('routes.login_page'))
    return render_template('login.html', error=error)


# Site Landing Page
@routes.route('/sign-up', methods=['GET', 'POST'])
def signup_page():
    if current_user.is_authenticated:
        if current_user.username == 'admin':
            return redirect(url_for('routes.admin'))
        else:
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
        # hash password
        hashedpassword = hashlib.sha512(password.encode('UTF-8')).hexdigest()
        if check:
            print('Username already exists')
            error = 'Username already exists'
        else:
            dbUser.create_user(username, hashedpassword, profilename, email, dob)
            print('Account Created')
            return redirect(url_for('routes.login_page'))
    return render_template('signup.html', error=error)


@routes.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('routes.login_page'))


# Error Site Route
# # Error handling page for not found sites / locations
# @app.errorhandler(404)
# def page_not_found(e):
#     return render_template('404.html'), 404
