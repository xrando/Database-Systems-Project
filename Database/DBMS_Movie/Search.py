import mariadb
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
def search_directors(name: str) -> tuple | None:
    search_stmt = "SELECT * " \
                  "FROM Director " \
                  "WHERE director_name " \
                  "LIKE ? " \
                  "LIMIT 30"
    try:
        cursor.execute(search_stmt, ('%' + name + '%',))
    except mariadb.DataError as e:
        print(f"[-] Error searching for directors from database\n {e}")
    return cursor.fetchall()


def search_movies(name: str) -> tuple | None:
    search_stmt = "SELECT * " \
                  "FROM Movie " \
                  "WHERE title " \
                  "LIKE ? " \
                  "LIMIT 30"
    try:
        cursor.execute(search_stmt, ('%' + name + '%',))
    except mariadb.DataError as e:
        print(f"[-] Error searching for movies from database\n {e}")
    return cursor.fetchall()


def search_actors(name: str) -> tuple | None:
    search_stmt = "SELECT * " \
                  "FROM Actor " \
                  "WHERE actor_name " \
                  "LIKE ? " \
                  "LIMIT 30"
    try:
        cursor.execute(search_stmt, ('%' + name + '%',))
    except mariadb.DataError as e:
        print(f"[-] Error searching for actors from database\n {e}")
    return cursor.fetchall()


def get_movieID(title: str) -> int | None:
    stmt = "SELECT movie_id " \
           "FROM Movie " \
           "WHERE title = ?"
    try:
        cursor.execute(stmt, (title,))
    except mariadb.DataError as e:
        print(f"[-] Error getting movie id from database\n {e}")
    return cursor.fetchone()[0]