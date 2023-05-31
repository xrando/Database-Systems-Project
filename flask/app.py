from flask import Flask, render_template, request, url_for, redirect, flash, app
from flask_login import LoginManager, login_required, UserMixin, login_user
from datetime import timedelta
import Database.Database as Database


login_manager = LoginManager()
app = Flask(__name__)
db = Database.Database()
login_manager.init_app(app)
app.config.update(
    TESTING=True,
    SECRET_KEY='192b9bdd22ab9ed4d12e236c78afcb9a393ec15f71bbf5dc987d54727823bcbf'
)


class User(UserMixin):
    def __init__(self, id):
        user_data = db.get_user_by_id(id)
        print(user_data)
        self.id = user_data[0]
        self.username = user_data[1]
        self.password = user_data[2]
        self.name = user_data[3]

@login_manager.user_loader
def load_user(user_id):
    # Retrieve the user from the database using the provided user_id
    user_data = db.get_user_by_id(user_id)
    if user_data:
        id, username, password, profilename = user_data
        return User(id)

    return None


# Site Landing Page
@app.route('/', methods=['GET', 'POST'])
def login_page():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        # Check if username and password are correct
        db_password = db.get_password_by_username(username)
        if db_password:
            if password == db_password[1]:
                print("Matched, logging in...")
                user = User(db.get_user_by_id(db_password[0])[0])
                login_user(user, remember=True, duration=timedelta(minutes=5))
                return redirect(url_for('home'))
        # if username == 'admin' and password == 'admin':
        #     user = User()
        #     login_user(user, remember=True, duration=timedelta(minutes=5))
        #     return redirect(url_for('home'))
        else:
            flash('Username or Password is incorrect')
            return redirect(url_for('login_page'))
    return render_template('login.html')


# Error Site Route
@app.route('/home')
@login_required
def home():
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
