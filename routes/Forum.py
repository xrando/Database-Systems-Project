from flask import render_template, request
from . import routes
import Database.DBMS_Movie as DBMS_Movie
from Config.ConfigManager import ConfigManager
import Database.User as DBUser

DBMS_Movie = DBMS_Movie
dbUser = DBUser.Database()
config_manager = ConfigManager()
config = config_manager.get_config()


@routes.route('/post', methods=['POST', 'GET'])
def post():
    return render_template('forum.html')