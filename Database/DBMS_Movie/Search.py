from .DB_Connect import DBConnection
from Config.ConfigManager import ConfigManager

# Initialize the config manager
config_manager = ConfigManager()

# Get the configuration
config = config_manager.get_config()

# This is only for DBMS_Movie, not User
connection = DBConnection().connection
cursor = connection.cursor()


# search
def search_directors(name: str) -> tuple:
    cursor.execute("SELECT * "
                   "FROM Director "
                   "WHERE director_name "
                   "LIKE %s"
                   "LIMIT 30", ('%' + name + '%',))
    return cursor.fetchall()


def search_movies(name: str) -> tuple:
    cursor.execute("SELECT * "
                   "FROM Movie "
                   "WHERE title "
                   "LIKE %s"
                   "LIMIT 30", ('%' + name + '%',))
    return cursor.fetchall()


def search_actors(name: str) -> tuple:
    cursor.execute("SELECT * "
                   "FROM Actor "
                   "WHERE actor_name "
                   "LIKE %s"
                   "LIMIT 30", ('%' + name + '%',))
    return cursor.fetchall()


def get_movieID(title: str) -> int:
    cursor.execute("SELECT movie_id "
                   "FROM Movie "
                   "WHERE title = %s", (title,))
    return cursor.fetchone()[0]
