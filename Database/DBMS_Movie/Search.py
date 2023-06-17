import mariadb
import configparser
import os

config = configparser.ConfigParser()
config_route = os.path.join(os.path.dirname(__file__), '..', '..', 'Config', 'config.ini')

try:
    config.read(config_route)
except configparser.Error as e:
    print(f"Error reading config file: {e}")

# This is only for DBMS_Movie, not User
conn = mariadb.connect(
    user=config.get('DBMS_MOVIE', 'USERNAME'),
    password=config.get('DBMS_MOVIE', 'PASSWORD'),
    host=config.get('DBMS_MOVIE', 'HOST'),
    port=int(config.get('DBMS_MOVIE', 'PORT')),
    database=config.get('DBMS_MOVIE', 'DATABASE')
)
cursor = conn.cursor()


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
    return self.cursor.fetchall()


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
