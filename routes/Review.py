from flask import request, redirect, url_for

import Database.DBMS_Movie as DBMS_Movie
from Config.ConfigManager import ConfigManager
from Database import Mongo
from . import routes

DBMS_Movie = DBMS_Movie
config_manager = ConfigManager()
config = config_manager.get_config()
handler = Mongo.MongoDBHandler.get_instance(
    config.get('MONGODB', 'CONNECTION_STRING'),
    config.get('MONGODB', 'DATABASE')
)


# review
@routes.route('/review', methods=['POST'])
def review():
    movieName = request.form['movie_name']
    rating = request.form['rating']
    comments = request.form['comment']
    # print(movieName)
    # print(rating)
    # print(comments)
    movieID = DBMS_Movie.check_movie(movieName)
    # print(movieID)
    # if movieID is None, create new movie document
    # print(handler.find_documents('reviews', {'movie_id': movieID}))
    if not handler.find_documents(config.get('MONGODB', 'REVIEW_COLLECTION'), {'movie_id': movieID}):
        handler.insert_document(config.get('MONGODB', 'REVIEW_COLLECTION'), {
            'movie_id': movieID,
            'ratings': [rating],
            'comments': [comments],
        }, True)
    # if movieID is found, append ratings and comments
    else:
        handler.update_document(config.get('MONGODB', 'REVIEW_COLLECTION'), {'movie_id': movieID}, {
            'ratings': rating,
            'comments': comments,
        }, '$push')
    # return to home page
    return redirect(url_for('routes.movie_page', movie_name=movieName))
