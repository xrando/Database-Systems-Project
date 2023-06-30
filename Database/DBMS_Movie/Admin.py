import mariadb
import tmdbsimple as tmdb
from .DB_Connect import DBConnection
from Config.ConfigManager import ConfigManager
import Database.Mongo as Mongo
import logging

# Initialize the config manager
config_manager = ConfigManager()

# Get the configuration
config = config_manager.get_config()

tmdb.API_KEY = config.get('TMDB', 'API_KEY')

connection = DBConnection().connection
cursor = connection.cursor()

handler = Mongo.MongoDBHandler.get_instance(
    config.get('MONGODB', 'CONNECTION_STRING'),
    config.get('MONGODB', 'DATABASE')
)


def updateMovie(movie_name: str = None, release_date: str = None, synopsis: str = None, movie_id: int = None) -> bool:
    if not all([movie_name, release_date, synopsis, movie_id]):
        return False

    try:
        with connection.cursor() as cursor:
            # Begin the transaction
            connection.begin()
            logging.info(f"Updating movie details for movie_id: {movie_id}")

            # Update the movie details
            update_stmt = "UPDATE Movie " \
                          "SET title = ?, release_date = ?, synopsis = ? " \
                          "WHERE movie_id = ?"

            cursor.execute(update_stmt, (movie_name, release_date, synopsis, movie_id))

            # Commit the transaction
            connection.commit()

            logging.info(f"Successfully updated movie details for movie_id: {movie_id}")

            return True

    except mariadb.Error as e:
        # print(f"[-] Error updating movie details from database\n {e}")
        logging.error(f"Error updating movie details from database\n {e}")
        # Rollback the transaction in case of an error
        connection.rollback()

    return False


def deleteMovie(movie_id: str = None) -> bool:
    if not movie_id:
        return False

    try:
        with connection.cursor() as cursor:
            # Begin the transaction
            connection.begin()
            logging.info(f"Deleting movie from database with movie_id: {movie_id}")

            # Delete from parent table
            parent_delete_stmt = "DELETE FROM Movie WHERE movie_id = ?"
            cursor.execute(parent_delete_stmt, (movie_id,))

            # Commit the transaction
            connection.commit()

            logging.info(f"Successfully deleted movie from database with movie_id: {movie_id}")

            return True

    except mariadb.Error as e:
        logging.error(f"Error deleting movie from database\n {e}")
        # Rollback the transaction in case of an error
        connection.rollback()

    return False


def update_movie_info(title: str = None, tmdb_id: int = None) -> bool:
    """
    Retrieve movie information from tmdb and update the database with either the title or tmdb_id

    :param title: title of the movie
    :type title: str
    :param tmdb_id: tmdb_id of the movie
    :type tmdb_id: int
    :return: True if successful, False otherwise
    """
    poster_link = config.get('MOVIE', 'TMDB_IMAGE_URL')
    data = handler.find_documents(config.get('MONGODB', 'MOVIE_INFO_COLLECTION'), {'title': title})
    new_poster = None
    new_banner = None
    new_rating = None
    movie_info = None

    try:
        if title:
            logging.info(f"Retrieving movie info from tmdb for title: {title}")
            movie_id = tmdb.Search().movie(query=title)['results'][0]['id']
            movie_info = tmdb.Movies(movie_id).info()
        elif tmdb_id:
            logging.info(f"Retrieving movie info from tmdb for tmdb_id: {tmdb_id}")
            movie_info = tmdb.Movies(tmdb_id).info()

        # Update the movie info in the database if the data does not match
        if movie_info is not None:
            if movie_info['poster_path'] is not None:
                new_poster = poster_link + movie_info['poster_path']
            else:
                new_poster = None
            if movie_info['backdrop_path'] is not None:
                new_banner = poster_link + movie_info['backdrop_path']
            else:
                new_banner = None
            try:
                new_rating = [movie_info['vote_average'], movie_info['vote_count']]
            except KeyError:
                new_rating = None

    except IndexError:
        print(f"[-] Error retrieving movie info from tmdb\n")
        return False

    try:
        if data[0]['poster'] != new_poster:
            handler.update_document(config.get('MONGODB', 'MOVIE_INFO_COLLECTION'), {'title': title},
                                    {'poster': new_poster})
        if data[0]['banner'] != new_banner:
            handler.update_document(config.get('MONGODB', 'MOVIE_INFO_COLLECTION'), {'title': title},
                                    {'banner': new_banner})
        if data[0]['rating'] != new_rating:
            handler.update_document(config.get('MONGODB', 'MOVIE_INFO_COLLECTION'), {'title': title},
                                    {'rating': new_rating})
    except IndexError:
        logging.error(f"Error retrieving movie info from tmdb for title: {title}")
        return False

    return True
