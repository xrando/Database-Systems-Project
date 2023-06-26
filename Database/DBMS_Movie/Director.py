import mariadb
import tmdbsimple as tmdb
from .DB_Connect import DBConnection
from Config.ConfigManager import ConfigManager
import Database.Mongo as Mongo

# Initialize the config manager
config_manager = ConfigManager()

# Get the configuration
config = config_manager.get_config()

connection = DBConnection().connection
cursor = connection.cursor()

# MongoDB Connection
handler = Mongo.MongoDBHandler(
    config.get('MONGODB', 'CONNECTION_STRING'),
    config.get('MONGODB', 'DATABASE')
)

tmdb.API_KEY = config.get('TMDB', 'API_KEY')


def Director(
        director_name: str = None,
        director_tmdb_id: str = None,
        order_by: list = None
) -> dict:
    """
    Get all movies a director has directed
    :param director_name: Director's name
    :type director_name: str
    :param director_tmdb_id: Director's tmdb_id
    :type director_tmdb_id: str
    :param order_by: Order by release_date or title, ASC or DESC
    :type order_by: list
    :return: List of movies (title, release_date) and director's profile from tmdb
    :rtype: dict
    """
    if order_by is None:
        order_by = ["release_date", "DESC"]
    movies = []
    orders = {"release_date": "release_date", "title": "title"}
    if order_by[0] not in orders:
        raise ValueError("order_by must be one of: release_date, title")
    if order_by[1] not in ["ASC", "DESC"]:
        raise ValueError("order_by[1] must be one of: ASC, DESC")

    stmt = "SELECT Movie.title, Movie.release_date " \
           "FROM Movie " \
           "INNER JOIN Movie_Director " \
           "ON Movie.movie_id = Movie_Director.movie_id " \
           "INNER JOIN Director " \
           "ON Movie_Director.director_id = Director.director_id "
    if director_name is not None and director_tmdb_id is None:
        stmt += "WHERE Director.director_name = ? "
    elif director_tmdb_id is not None and director_name is None:
        stmt += "WHERE Director.tmdb_id = ? "
    else:
        raise ValueError("Either ONE director_name or director_tmdb_id must be specified")

    stmt += f"ORDER BY {orders[order_by[0]]} {order_by[1]}"
    try:
        cursor.execute(stmt, (director_name or director_tmdb_id,))
        movies = cursor.fetchall()
    except mariadb.Error as e:
        print(f"Error: {e}")
        return {"movies": [], "director": None}

    result = []
    for movie in movies:
        result += [(movie[0], movie[1].strftime("%B %d, %Y"))]

    director_info = None
    if director_tmdb_id:
        director_info = get_director_info(int(director_tmdb_id))

    elif director_name:
        stmt = "SELECT tmdb_id " \
               "FROM Director " \
               "WHERE director_name = ?"
        try:
            cursor.execute(stmt, (director_name,))
            director_tmdb_id = cursor.fetchone()[0]
        except [mariadb.Error, TypeError] as e:
            print(f"Error getting director's tmdb_id: {e}")

        if director_tmdb_id is not None:
            director_info = get_director_info(int(director_tmdb_id))
    else:
        raise ValueError("Either ONE director_name or director_tmdb_id must be specified")

    return {"movies": result, "director": director_info}


def get_director_info(director_tmdb_id: int) -> dict:
    """
    Get director's info from mongodb or tmdb
    :param director_tmdb_id: Director's tmdb_id
    :type director_tmdb_id: int
    :return: Director's info
    :rtype: dict
    """
    data = handler.find_documents(
        config.get('MONGODB', 'DIRECTOR_INFO_COLLECTION'),
        {"_id": director_tmdb_id}
    )
    if data is None or data == []:
        try:
            data = tmdb.People(director_tmdb_id).info()
            handler.insert_document(
                config.get('MONGODB', 'DIRECTOR_INFO_COLLECTION'),
                {"_id": director_tmdb_id, "data": data}
            )
        except IndexError:
            data = None
    else:
        data = data[0]["data"]

    return data
