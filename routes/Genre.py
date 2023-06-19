from flask import render_template

import Database.DBMS_Movie as DBMS_Movie
import Database.Mongo as Mongo
from Config.ConfigManager import ConfigManager
from . import routes

DBMS_Movie = DBMS_Movie
config_manager = ConfigManager()
config = config_manager.get_config()

handler = Mongo.MongoDBHandler('mongodb://localhost:27017/', 'movie_db')


@routes.route('/genre/<genre>/<int:page>', methods=['GET'])
@routes.route('/genre/<genre>', defaults={'page': 1}, methods=['GET'])
def genre_page(genre: str, page: int) -> str:
    if genre is None:
        # TODO: Convert to error page
        raise Exception('Genre not found')
    limit = int(config.get("MOVIE", "LIMIT"))
    pages = DBMS_Movie.get_genre_pages(genre=genre, limit=limit)
    pages_left = pages["pages_left"]
    total_pages = pages["total_pages"]

    # TODO: Convert to error page
    if page < 1:
        raise Exception('Page not found')
    elif page > total_pages:
        raise Exception('Page not found')

    movie_list = DBMS_Movie.Genre(genre=genre, page=page, limit=limit)
    kwargs = {'genre': genre}  # Additional keyword arguments for the URL

    return render_template(
        'index.html',
        endpoint='routes.genre_page',
        movie_list=movie_list,
        total_pages=total_pages,
        pages_left=pages_left,
        page=page,
        kwargs=kwargs
    )