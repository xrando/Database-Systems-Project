import flask_login
from flask import Flask, render_template, request, url_for, redirect, flash, app
from flask_login import LoginManager, login_required, UserMixin, login_user
from datetime import timedelta
import Database.Database as Database


# from . import db

class User(UserMixin):
    id = "1"  # primary keys are required by SQLAlchemy
    username = "admin@email.com"
    password = "admin"
    name = "admin"
    is_active = True  # Change to True



login_manager = LoginManager()
app = Flask(__name__)
login_manager.init_app(app)
app.config.update(
    TESTING=True,
    SECRET_KEY='192b9bdd22ab9ed4d12e236c78afcb9a393ec15f71bbf5dc987d54727823bcbf'
)


@login_manager.user_loader
def load_user(user_id):
    if user_id == User.id:
        return User


# Site Landing Page
@app.route('/', methods=['GET', 'POST'])
def login_page():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        # Check if username and password are correct
        if username == 'admin' and password == 'admin':
            user = User()
            login_user(user, remember=True, duration=timedelta(minutes=5))
            return redirect(url_for('home'))
        else:
            flash('Username or Password is incorrect')
            return redirect(url_for('login'))
    return render_template('login.html')


# Error Site Route
@app.route('/home')
@login_required
def home():
    db = Database.Database()
    movie_list = db.Movie_list(page=8, limit=12)
    pages = db.get_pages_left(pages=8, limit=12)
    carousel = db.carousel()

    return render_template('index.html', movie_list=movie_list, pages=pages, carousel=carousel)


# # Error handling page for not found sites / locations
# @app.errorhandler(404)
# def page_not_found(e):
#     return render_template('404.html'), 404


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
