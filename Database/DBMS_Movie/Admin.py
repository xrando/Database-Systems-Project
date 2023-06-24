import mariadb
import tmdbsimple as tmdb
from .DB_Connect import DBConnection
from Config.ConfigManager import ConfigManager

# Initialize the config manager
config_manager = ConfigManager()

# Get the configuration
config = config_manager.get_config()

tmdb.API_KEY = config.get('TMDB', 'API_KEY')

connection = DBConnection().connection
cursor = connection.cursor()


# def updateMovie(movie_name: str = None, release_date: str = None, synopsis: str = None) -> bool:
#     update_stmt = "UPDATE Movie " \
#                   "SET title = ?, release_date = ?, synopsis = ?" \
#                   "WHERE title = ?"
#     try:
#         cursor.execute(update_stmt, (movie_name, release_date, synopsis))
#     except mariadb.DataError as e:
#         print(f"[-] Error updating movie details from database\n {e}")
#     movies = cursor.fetchall()
#     print(movies)
#     return True


def deleteMovie(movie_id: str = None) -> bool:
    # delete from child (movie_actor, movie_director, movie_genre)
    actor_stmt = "DELETE FROM Movie_Actor " \
                 "WHERE movie_id = ?"
    try:
        cursor.execute(actor_stmt, (movie_id,))
    except mariadb.DataError as e:
        print(f"[-] Error deleting movie_actor from database\n {e}")
    director_stmt = "DELETE FROM Movie_Director " \
                    "WHERE movie_id = ?"
    try:
        cursor.execute(director_stmt, (movie_id,))
    except mariadb.DataError as e:
        print(f"[-] Error deleting movie_director from database\n {e}")
    genre_stmt = "DELETE FROM Movie_Genre " \
                 "WHERE movie_id = ?"
    try:
        cursor.execute(genre_stmt, (movie_id,))
    except mariadb.DataError as e:
        print(f"[-] Error deleting movie_genre from database\n {e}")

    # delete from parent (movie)
    delete_stmt = "DELETE FROM Movie " \
                  "WHERE movie_id = ?"
    try:
        cursor.execute(delete_stmt, (movie_id,))
    except mariadb.DataError as e:
        print(f"[-] Error deleting movie from database\n {e}")
    return True
