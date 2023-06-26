from flask import render_template, request
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

@routes.route('/search', methods=['POST'])
def search():
    query = request.form['search'].strip()
    if query:
        director_results = DBMS_Movie.search_directors(query)
        actor_results = DBMS_Movie.search_actors(query)
        movie_results = DBMS_Movie.search_movies(query)
        profile_results = dbUser.search_user(query)
        return render_template('search.html', directors=director_results, actors=actor_results, movies=movie_results, profiles=profile_results)
    return render_template('search.html')

@routes.route('/searchMovie', methods=['POST'])
def search_query():
    query = request.form['search'].strip()
    movies = DBMS_Movie.search_movies(query)
    #grab all updated posts
    allPosts = handler.find_documents(config.get('MONGODB', 'FORUM_COLLECTION'), {})
    #grab all movie requests
    allRequests = handler.find_documents(config.get('MONGODB', 'REQUEST_COLLECTION'), {})
    return render_template('admin.html', movies=movies, posts = allPosts, requests = allRequests)