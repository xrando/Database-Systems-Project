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


def updateMovie(movie_name: str = None, release_date: str = None, synopsis: str = None) -> bool:
    update_stmt = "UPDATE Movie " \
                  "SET title = ?, release_date = ?, synopsis = ?" \
                  "WHERE title = ?"
    try:
        cursor.execute(update_stmt, (movie_name, release_date, synopsis))
    except mariadb.DataError as e:
        print(f"[-] Error updating movie details from database\n {e}")
    movies = cursor.fetchall()
    print(movies)
    return True


def deleteMovie(movie_name: str = None) -> bool:
    delete_stmt = "DELETE FROM Movie " \
                  "WHERE title = ?"
    try:
        cursor.execute(delete_stmt, (movie_name,))
    except mariadb.DataError as e:
        print(f"[-] Error deleting movie from database\n {e}")
    movies = cursor.fetchall()
    print(movies)
    return True