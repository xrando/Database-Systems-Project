import configparser

from flask import request, redirect

import Database.DBMS_Movie as DBMS_Movie
from Database import Mongo
import os
from . import routes

DBMS_Movie = DBMS_Movie
config = configparser.ConfigParser()
config_route = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'Config', 'config.ini'))
config.read(config_route)
handler = Mongo.MongoDBHandler('mongodb://localhost:27017/', 'movie_db')


# review
@routes.route('/review', methods=['POST'])
def review():
    movieName = request.form['movie_name']
    rating = request.form['rating']
    comments = request.form['comment']
    # print(movieName)
    # print(rating)
    # print(comments)
    movieID = DBMS_Movie.get_movieID(movieName)
    # print(movieID)
    # if movieID is None, create new movie document
    # print(handler.find_documents('reviews', {'movie_id': movieID}))
    if handler.find_documents('reviews', {'movie_id': movieID}) == []:
        handler.insert_document('reviews', {
            'movie_id': movieID,
            'ratings': [rating],
            'comments': [comments],
        })
    # if movieID is found, append ratings and comments
    else:
        handler.update_document('reviews', {'movie_id': movieID}, {
            'ratings': rating,
            'comments': comments,
        }, '$push')
    # return to home page
    return redirect('/')
