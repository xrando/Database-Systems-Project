import mariadb
import tmdbsimple as tmdb
from .DB_Connect import DBConnection
from .ConfigManager import ConfigManager

# Initialize the config manager
config_manager = ConfigManager()

# Get the configuration
config = config_manager.get_config()

connection = DBConnection().connection
cursor = connection.cursor()

tmdb.API_KEY = config.get('TMDB', 'API_KEY')


def Actor(actor_name: str = None, actor_tmdb_id: str = None, order_by=None) -> dict:
    """
    Get All movies an actor has been in, and their roles

    Used for the actor page

    :param actor_name: Actor's name
    :type actor_name: str
    :param actor_tmdb_id: Actor's tmdb id
    :type actor_tmdb_id: str
    :param order_by: Order by release_date or title, ASC or DESC
    :type order_by: list
    :return: List of movies (title, release_date, movie_character) and actor's profile from tmdb
    :rtype: dict
    """
    movies = []
    if order_by is None:
        order_by = ["release_date", "DESC"]
    orders = {"release_date": "release_date", "title": "title", "movie_id": "movie_id"}
    if order_by[0] not in orders:
        raise ValueError(f"order_by[0] must be one of {list(orders.keys())}")

    stmt = "SELECT Movie.title, Movie.release_date, Movie_Actor.movie_character " \
           "FROM Movie INNER JOIN Movie_Actor " \
           "ON Movie.movie_id = Movie_Actor.movie_id " \
           "INNER JOIN Actor " \
           "ON Movie_Actor.actor_id = Actor.actor_id "

    if actor_name and not actor_tmdb_id:
        stmt += "WHERE Actor.actor_name = ? "
    elif actor_tmdb_id and not actor_name:
        stmt += "WHERE Actor.tmdb_id = ? "
    else:
        raise ValueError("Either ONE actor_name or actor_tmdb_id must be specified")

    # SQL Statements cannot be parameterized for ORDER BY, Parameters are sanitized by above code
    stmt += f"ORDER BY {orders[order_by[0]]} {order_by[1]}"

    try:
        cursor.execute(stmt, (actor_name or actor_tmdb_id,))
        movies = cursor.fetchall()
    except mariadb.Error as e:
        print(f"Error getting movies: {e}")

    movie_result = []
    for movie in movies:
        movie_result.append((movie[0], movie[1].strftime("%d %B %Y"), movie[2]))

    # Get actor's detail from DB
    if actor_tmdb_id:
        stmt = "SELECT actor_name " \
               "FROM Actor " \
               "WHERE tmdb_id = ?"
        try:
            cursor.execute(stmt, (actor_tmdb_id,))
            actor_name = cursor.fetchone()[0]
        except mariadb.Error as e:
            print(f"Error getting actor's name: {e}")

        try:
            actor_info = tmdb.People(actor_tmdb_id).info()
        except IndexError:
            actor_info = None
    elif actor_name:
        stmt = "SELECT tmdb_id " \
               "FROM Actor " \
               "WHERE actor_name = ?"
        try:
            cursor.execute(stmt, (actor_name,))
            actor_tmdb_id = cursor.fetchone()[0]
        except [mariadb.Error, TypeError] as e:
            print(f"Error getting actor's tmdb_id: {e}")

        if actor_tmdb_id is not None:
            try:
                actor_info = tmdb.People(actor_tmdb_id).info()
            except IndexError:
                actor_info = None
    else:
        actor_info = None

    return {"movies": movie_result, "actor": actor_info}
