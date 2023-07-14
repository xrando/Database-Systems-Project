from flask import render_template, request, abort
from . import routes
import Database.DBMS_Movie as DBMS_Movie
from Config.ConfigManager import ConfigManager
import Database.User as DBUser
from Database import Mongo
import logging

DBMS_Movie = DBMS_Movie
dbUser = DBUser.Database()
config_manager = ConfigManager()
config = config_manager.get_config()
handler = Mongo.MongoDBHandler.get_instance(
    config.get('MONGODB', 'CONNECTION_STRING'),
    config.get('MONGODB', 'DATABASE')
)

def load_stats():
    #get statistics
    data = {'Genre' : 'Popularity Score'}
    #get total popularity of all movies
    allRating = handler.find_documents(config.get('MONGODB', 'REVIEW_COLLECTION'), {}, 0)
    for rating in allRating:
        totalScore = 0
        for score in rating['ratings']:
            #add all scores together
            totalScore += int(score)
        #if genre already exists, add to it
        if DBMS_Movie.get_genre_name(DBMS_Movie.get_genre(rating['movie_id'])) in data:
            data[DBMS_Movie.get_genre_name(DBMS_Movie.get_genre(rating['movie_id']))] += int(totalScore)
        #else create new genre
        else:
            data[DBMS_Movie.get_genre_name(DBMS_Movie.get_genre(rating['movie_id']))] = int(totalScore)
        logging.info(data)
    return data

@routes.route('/search', methods=['POST'])
def search():
    query = request.form['search'].strip()
    if query:
        director_results = DBMS_Movie.search_directors(query)
        actor_results = DBMS_Movie.search_actors(query)
        movie_results = DBMS_Movie.search_movies(query)
        profile_results = dbUser.search_user(query)
        return render_template('search.html', directors=director_results, actors=actor_results, movies=movie_results, profiles=profile_results)
    else:
        abort(404)
        logging.error("No search input provided")

@routes.route('/searchMovie', methods=['POST'])
def search_query():
    query = request.form['search'].strip()
    #return error page if no results
    if not query:
        abort(404)
        logging.error("No movie provided")
    movies = DBMS_Movie.search_movies(query)
    #grab all updated posts
    allPosts = handler.find_documents(config.get('MONGODB', 'FORUM_COLLECTION'), {})
    #grab all movie requests
    allRequests = handler.find_documents(config.get('MONGODB', 'REQUEST_COLLECTION'), {})
    #load statistics
    data = load_stats()
    return render_template('admin.html', movies=movies, posts = allPosts, requests = allRequests, data=data)

# search posts by subject
@routes.route('/searchPosts', methods=['POST'])
def searchPost():
    subject = request.form['search']
    #return error page if no results
    if not subject:
        abort(404)
        logging.error("No subject provided")
    # grab all posts with subject
    allPosts = handler.find_documents(config.get('MONGODB', 'FORUM_COLLECTION'), {'subject': subject})
    #grab all movie requests
    allRequests = handler.find_documents(config.get('MONGODB', 'REQUEST_COLLECTION'), {})
    data = load_stats()
    return render_template('admin.html', posts=allPosts, data=data, requests = allRequests)