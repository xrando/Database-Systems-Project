import logging

import mariadb

from Config.ConfigManager import ConfigManager
from .DB_Connect import DBConnection
from .. import Mongo

# Initialize the config manager
config_manager = ConfigManager()

# Get the configuration
config = config_manager.get_config()

handler = Mongo.MongoDBHandler.get_instance(
    config.get('MONGODB', 'CONNECTION_STRING'),
    config.get('MONGODB', 'DATABASE')
)

# This is only for DBMS_Movie
connection = DBConnection().connection
cursor = connection.cursor()


def search_directors(name: str) -> tuple or None:
    search_stmt = "SELECT * FROM Director WHERE director_name LIKE ? LIMIT 30"
    term_data = handler.find_documents(config.get('MONGODB', 'SEARCH_CACHE_COLLECTION'),
                                       {'term': name, 'type': 'directors'})

    if term_data:
        data = term_data[0]['data']
        if data:
            return data

    try:
        cursor.execute(search_stmt, ('%' + name + '%',))
    except mariadb.DataError as e:
        logging.error(f"Error searching for directors from the database: {e}")
        return None

    data = cursor.fetchall()

    if not data:
        return []

    handler.insert_document(config.get('MONGODB', 'SEARCH_CACHE_COLLECTION'),
                            {'term': name, 'type': 'directors', 'data': data})

    return data


def search_movies(name: str) -> tuple or None:
    search_stmt = "SELECT * FROM Movie WHERE title LIKE ? LIMIT 30"
    term_data = handler.find_documents(config.get('MONGODB', 'SEARCH_CACHE_COLLECTION'),
                                       {'term': name, 'type': 'movies'})

    if term_data:
        data = term_data[0]['data']
        if data:
            return data

    try:
        cursor.execute(search_stmt, ('%' + name + '%',))
    except mariadb.DataError as e:
        logging.error(f"Error searching for movies from the database: {e}")
        return None

    data = cursor.fetchall()

    if not data:
        return []

    handler.insert_document(config.get('MONGODB', 'SEARCH_CACHE_COLLECTION'),
                            {'term': name, 'type': 'movies', 'data': data})

    return data


def search_actors(name: str) -> tuple or None:
    search_stmt = "SELECT * FROM Actor WHERE actor_name LIKE ? LIMIT 30"
    term_data = handler.find_documents(config.get('MONGODB', 'SEARCH_CACHE_COLLECTION'),
                                       {'term': name, 'type': 'actors'})

    if term_data:
        data = term_data[0]['data']
        if data:
            return data

    try:
        cursor.execute(search_stmt, ('%' + name + '%',))
    except mariadb.DataError as e:
        logging.error(f"Error searching for actors from the database: {e}")
        return None

    data = cursor.fetchall()

    if not data:
        return []

    handler.insert_document(config.get('MONGODB', 'SEARCH_CACHE_COLLECTION'),
                            {'term': name, 'type': 'actors', 'data': data})

    return data

# def get_movieID(title: str) -> int | None:
#     stmt = "SELECT movie_id " \
#            "FROM Movie " \
#            "WHERE title = ?"
#     try:
#         cursor.execute(stmt, (title,))
#     except mariadb.DataError as e:
#         loging = logging.error(f"Error getting movie_id from database\n {e}")
#     return cursor.fetchone()[0]
