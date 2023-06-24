from bson import ObjectId
from flask import render_template, request, redirect, url_for
from . import routes
import Database.DBMS_Movie as DBMS_Movie
from Config.ConfigManager import ConfigManager
import Database.User as DBUser
from Database import Mongo

DBMS_Movie = DBMS_Movie
dbUser = DBUser.Database()
config_manager = ConfigManager()
config = config_manager.get_config()
handler = Mongo.MongoDBHandler(config.get('MONGODB', 'CONNECTION_STRING'), config.get('MONGODB', 'DATABASE'))



@routes.route('/admin', methods=['GET'])
def admin():
    #grab all updated posts
    allPosts = handler.find_documents(config.get('MONGODB', 'FORUM_COLLECTION'), {})
    #print(allPosts)
    return render_template('admin.html', posts = allPosts)

#test data, title=aang, tmdb_id=172687
@routes.route('/addMovie', methods=['POST'])
def addMovie():
    movie_name = request.form['movie_name']
    tmdb_id = request.form['tmdb_id']
    print(movie_name, tmdb_id)
    DBMS_Movie.new_movie(movie_name, tmdb_id)
    return redirect(url_for('routes.movie_page', movie_name=movie_name))
    #return redirect(url_for('routes.admin'))


@routes.route('/deleteMovie/<string:movie_name>', methods=['GET'])
def deleteMovie(movie_name: str = None):
    print(movie_name)
    #dependancy issues when deleting
    if movie_name:
        DBMS_Movie.deleteMovie(movie_name)
    return redirect(url_for('routes.admin'))

@routes.route('/deletePost/<string:postID>', methods=['GET'])
def deletePost(postID: str = None):
    print(postID)
    #delete from mongodb
    handler.delete_documents(config.get('MONGODB', 'FORUM_COLLECTION'), {'_id': ObjectId(postID)})
    return redirect(url_for('routes.admin'))