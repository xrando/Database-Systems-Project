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
    # cursor.execute("SELECT * "
    #                "FROM Director "
    #                "WHERE director_name "
    #                "LIKE %s"
    #                "LIMIT 30", ('%' + name + '%',))
    search_stmt = "SELECT * " \
                  "FROM Director " \
                  "WHERE director_name " \
                  "LIKE ? " \
                  "LIMIT 30"
    cursor.execute(search_stmt, ('%' + name + '%',))
    return cursor.fetchall()


def search_movies(name: str) -> tuple | None:
    # cursor.execute("SELECT * "
    #                "FROM Movie "
    #                "WHERE title "
    #                "LIKE %s"
    #                "LIMIT 30", ('%' + name + '%',))
    search_stmt = "SELECT * " \
                  "FROM Movie " \
                  "WHERE title " \
                  "LIKE ? " \
                  "LIMIT 30"
    cursor.execute(search_stmt, ('%' + name + '%',))
    return cursor.fetchall()


def search_actors(name: str) -> tuple | None:
    # cursor.execute("SELECT * "
    #                "FROM Actor "
    #                "WHERE actor_name "
    #                "LIKE %s"
    #                "LIMIT 30", ('%' + name + '%',))
    search_stmt = "SELECT * " \
                  "FROM Actor " \
                  "WHERE actor_name " \
                  "LIKE ? " \
                  "LIMIT 30"
    cursor.execute(search_stmt, ('%' + name + '%',))
    return cursor.fetchall()


def get_movieID(title: str) -> int | None:
    # cursor.execute("SELECT movie_id "
    #                "FROM Movie "
    #                "WHERE title = %s", (title,))
    stmt = "SELECT movie_id " \
           "FROM Movie " \
           "WHERE title = ?"
    cursor.execute(stmt, (title,))
    return cursor.fetchone()[0]
