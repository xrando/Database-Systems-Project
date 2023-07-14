import logging

from flask import render_template, request, redirect, abort

import Database.DBMS_Movie as DBMS_Movie
import Database.Mongo as Mongo
from Config.ConfigManager import ConfigManager
from . import routes

DBMS_Movie = DBMS_Movie
config_manager = ConfigManager()
config = config_manager.get_config()

handler = Mongo.MongoDBHandler.get_instance(
    config.get('MONGODB', 'CONNECTION_STRING'),
    config.get('MONGODB', 'DATABASE')
)


@routes.route('/genre/<genre>/<int:page>', methods=['GET'])
@routes.route('/genre/<genre>', defaults={'page': 1}, methods=['GET'])
def genre_page(genre: str, page: int) -> str:
    if genre is None:
        abort(404)
    limit = int(config.get("MOVIE", "LIMIT"))
    pages = DBMS_Movie.get_genre_pages(genre=genre, limit=limit)
    pages_left = pages["pages_left"]
    total_pages = pages["total_pages"]

    if page < 1:
        abort(404)
        logging.error("Page is less than 1")
    elif page > total_pages:
        abort(404)
        logging.error("Page is greater than total pages")

    movie_list = DBMS_Movie.Genre(genre=genre, page=page, limit=limit)
    carousel = DBMS_Movie.carousel()
    genres = DBMS_Movie.get_all_genres()
    kwargs = {'genre': genre}  # Additional keyword arguments for the URL

    return render_template(
        'index.html',
        endpoint='routes.genre_page',
        movie_list=movie_list,
        total_pages=total_pages,
        pages_left=pages_left,
        page=page,
        carousel=carousel,
        genre=genre,
        genre_list=genres,
        kwargs=kwargs
    )

@routes.route('/filter', methods=['POST'])
def filterGenre():
    genre = request.form['genre']
    return redirect('/genre/' + genre + '/1')