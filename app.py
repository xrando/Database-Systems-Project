from flask import Flask
from flask_login import LoginManager

from routes import *
from Config.ConfigManager import ConfigManager

app = Flask(__name__)
login_manager = LoginManager()
login_manager.init_app(app)
config_manager = ConfigManager()
config = config_manager.get_config()

app.config.update(TESTING=True, SECRET_KEY='192b9bdd22ab9ed4d12e236c78afcb9a393ec15f71bbf5dc987d54727823bcbf')
app.register_blueprint(routes)


@login_manager.user_loader
def load_user(user_id):
    dbUser = DBUser.Database()
    # Retrieve the user from the database using the provided user_id
    user_data = dbUser.get_user_by_id(user_id)
    # print("User_loader is running")
    # print(user_data)
    if user_data:
        return User(user_data[0])
    return None


# 404 Error
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


if __name__ == '__main__':
    app.run(
        host=config.get('FLASK', 'HOST'),
        port=int(config.get('FLASK', 'PORT')),
        debug=bool(config.get('FLASK', 'DEBUG'))
    )
