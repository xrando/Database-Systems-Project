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


def Movie_list(page: int = 1, limit: int = 30) -> list[tuple]:
    """
    Get all movies in the database, for the home page (30 most recent)

    Used to show movies in the home page.

    :param page: Page number (For Frontend)
    :type page: int
    :param limit: Number of movies per page
    :type limit: int
    :return: List of movies (title, release_date, synopsis, poster_link, banner_link)
    :rtype: list[tuple]
    """

    poster_link = config.get("MOVIE", "TMDB_IMAGE_URL")
    default_poster_link = config.get("MOVIE", "DEFAULT_POSTER_URL")
    default_banner_link = config.get("MOVIE", "DEFAULT_BANNER_URL")
    result = []
    offset = (page - 1) * limit

    stmt = "SELECT title, release_date, synopsis " \
           "FROM Movie " \
           "WHERE release_date < CURRENT_DATE() " \
           "ORDER BY release_date DESC " \
           "LIMIT ? " \
           "OFFSET ?;"
    cursor.execute(stmt, (limit, offset))
    movies = cursor.fetchall()
    for movie in movies:
        # Use tmdb api to get the image link
        try:
            movie_id = tmdb.Search().movie(query=movie[0])['results'][0]['id']
            movie_info = tmdb.Movies(movie_id).info()

            if movie_info is not None:
                if movie_info['poster_path'] is not None:
                    poster = poster_link + movie_info['poster_path']
                else:
                    poster = default_poster_link
                if movie_info['backdrop_path'] is not None:
                    banner = poster_link + movie_info['backdrop_path']
                else:
                    banner = default_banner_link
            else:
                poster = default_poster_link
                banner = default_banner_link
        except IndexError:
            # Not all movies we have in the database are in the tmdb database
            continue

        # Movie title + (year)
        movie_title = movie[0] + " (" + movie[1].strftime("%Y") + ")"
        # Convert date to string
        movie_date = movie[1].strftime("%d %B %Y")

        # Shorten synopsis
        synopsis = movie[2][:100] + "..."
        result += [(movie_title, movie_date, synopsis, poster, banner)]

    return result


def get_movie_by_title(title: str) -> dict:
    """
    Get a movie by title as a dictionary of the following format:

    movie: (title, release_date, synopsis, poster_link, banner_link, movie_id)

    genres: [genre_name]

    director: (director_name, director tmdb link)

    actors: (actor_name, actor tmdb link, character)

    Used for the movie page to display all the information about a movie

    :param title: Movie title
    :return: Movie dictionary
    :rtype: dict
    """
    result = {}
    poster_link = config.get('MOVIE', 'TMDB_IMAGE_URL')

    movie_stmt = "Select Movie.title as movie_title, Movie.release_date, Movie.synopsis, Movie.movie_id " \
                 "FROM Movie " \
                 "WHERE Movie.title = ?"
    director_stmt = "SELECT Director.director_name as director_name, Director.tmdb_id as director_tmdb_id " \
                    "FROM Director INNER JOIN Movie_Director " \
                    "ON Director.director_id = Movie_Director.director_id " \
                    "INNER JOIN Movie " \
                    "ON Movie.movie_id = Movie_Director.movie_id " \
                    "WHERE Movie.title = ?"
    actor_stmt = "SELECT Actor.actor_name as actor_name, Actor.tmdb_id as actor_tmdb_id, " \
                 "Movie_Actor.movie_character " \
                 "FROM Actor INNER JOIN Movie_Actor " \
                 "ON Actor.actor_id = Movie_Actor.actor_id " \
                 "INNER JOIN Movie " \
                 "ON Movie.movie_id = Movie_Actor.movie_id " \
                 "WHERE Movie.title = ?"
    genre_stmt = "SELECT Genre.name as genre_name " \
                 "FROM Genre INNER JOIN Movie_Genre " \
                 "ON Genre.genre_id = Movie_Genre.genre_id " \
                 "INNER JOIN Movie " \
                 "ON Movie.movie_id = Movie_Genre.movie_id " \
                 "WHERE Movie.title = ?"
    try:
        cursor.execute(movie_stmt, (title,))
        movie = cursor.fetchone()
        try:
            movie_id = tmdb.Search().movie(query=movie[0])['results'][0]['id']
            movie_info = tmdb.Movies(movie_id).info()

            if movie_info is not None:
                if movie_info['poster_path'] is not None:
                    poster = poster_link + movie_info['poster_path']
                else:
                    poster = None
                if movie_info['backdrop_path'] is not None:
                    banner = poster_link + movie_info['backdrop_path']
                else:
                    banner = None
            else:
                poster = None
                banner = None
        except IndexError:
            # Not all movies we have in the database are in the tmdb database
            poster = None

        # Convert date to string
        movie_date = movie[1].strftime("%d %B %Y")

        result["movie"] = (movie[0], movie_date, movie[2], poster, banner, movie[3])

        cursor.execute(director_stmt, (title,))
        director = cursor.fetchone()

        director_tmdb_id = director[1]
        # director_name = director[0].replace(" ", "-")
        # director_link = config.get("MOVIE", "TMDB_PERSON_URL") + director_tmdb_id + "-" + director_name
        result["director"] = (director[0], director_tmdb_id)

        cursor.execute(actor_stmt, (title,))
        actors = cursor.fetchall()
        result["actors"] = list(actors)

        cursor.execute(genre_stmt, (title,))
        genres = cursor.fetchall()
        result["genres"] = [genre[0] for genre in genres]
        result["tmdb_link"] = config.get("MOVIE", "TMDB_MOVIE_URL") + str(movie_id)
    except mariadb.Error as e:
        print(f"Error executing statement: {e}")

    return result


def get_pages(pages: int = 1, limit: int = 30) -> dict[str, int]:
    """
    Get the number of pages
    :param pages: Number of pages
    :type pages: int
    :param limit: Number of movies per page
    :type limit: int
    :return: total_pages, pages_left
    :rtype: dict[str, int]
    """
    stmt = "SELECT ceil(count(*) / ?), ceil(count(*) / ?) - ? " \
           "FROM Movie " \
           "WHERE release_date < CURRENT_DATE();"

    cursor.execute(stmt, (limit, limit, pages))
    total_pages, pages_left = cursor.fetchone()
    return {"total_pages": total_pages, "pages_left": pages_left}


def carousel() -> list[tuple]:
    """
    Returns a list of 5 movies that are within 1 month of current date and have a banner image
    :return: List of movies (title, release_date, banner)
    :rtype: list[tuple]
    """
    poster_link = config.get("MOVIE", "TMDB_IMAGE_URL")
    result = []
    current_offset = 0

    stmt = "SELECT title, release_date " \
           "FROM Movie " \
           "WHERE release_date " \
           "BETWEEN CURRENT_DATE() - INTERVAL 1 MONTH " \
           "AND CURRENT_DATE() + INTERVAL 1 MONTH " \
           "ORDER BY release_date ASC " \
           "LIMIT 1 " \
           "OFFSET ?;"

    while len(result) < 5:
        cursor.execute(stmt, (len(result) + current_offset,))
        movie = cursor.fetchone()
        # Check if movie is in result (duplicate)
        if movie[0] in [x[0] for x in result]:
            current_offset += 1
            continue
        # Get movie info from tmdb api
        try:
            movie_id = tmdb.Search().movie(query=movie[0])['results'][0]['id']
            movie_info = tmdb.Movies(movie_id).info()
        except IndexError:
            # Not all movies we have in the database are in the tmdb database
            current_offset += 1
            continue
        except TypeError:  # Not all movies we have in the database are in the tmdb database
            current_offset += 1
            continue

        if movie_info is not None:
            if movie_info['backdrop_path'] is not None:
                banner = poster_link + movie_info['backdrop_path']
            else:
                current_offset += 1
                continue

        # Convert date to string
        movie_date = movie[1].strftime("%d %B %Y")
        result += [(movie[0], movie_date, banner)]

    return result


def Genre(genre: str = None, page: int = 1, limit: int = 30) -> list[tuple]:
    """
    Returns a list of genres
    :return: List of genres (genre_id, name)
    :return: List of movies (title, release_date, poster)
    :rtype: list[tuple]
    """
    if genre is None:
        stmt = "SELECT genre_id, name " \
               "FROM Genre;"

        cursor.execute(stmt)
        result = cursor.fetchall()

    else:
        stmt = "SELECT * " \
               "FROM Movie " \
               "INNER JOIN Movie_Genre " \
               "ON Movie.movie_id = Movie_Genre.movie_id " \
               "INNER JOIN Genre " \
               "ON Movie_Genre.genre_id = Genre.genre_id " \
               "WHERE Genre.name = ? " \
               "AND release_date <> '2045-05-31' " \
               "ORDER BY Movie.release_date DESC, " \
               "Movie.title " \
               "LIMIT ? " \
               "OFFSET ?;"

        cursor.execute(stmt, (genre, limit, (page - 1) * limit))
        movies = cursor.fetchall()

        poster_link = config.get("MOVIE", "TMDB_IMAGE_URL")
        default_poster_link = config.get("MOVIE", "DEFAULT_POSTER_URL")
        default_banner_link = config.get("MOVIE", "DEFAULT_BANNER_URL")
        result = []

        # Convert date to string
        for movie in movies:
            # Use tmdb api to get the image link
            try:
                movie_id = tmdb.Search().movie(query=movie[1])['results'][0]['id']
                movie_info = tmdb.Movies(movie_id).info()

                if movie_info is not None:
                    if movie_info['poster_path'] is not None:
                        poster = poster_link + movie_info['poster_path']
                    else:
                        poster = default_poster_link
                    if movie_info['backdrop_path'] is not None:
                        banner = poster_link + movie_info['backdrop_path']
                    else:
                        banner = default_banner_link
                else:
                    poster = default_poster_link
                    banner = default_banner_link
            except IndexError:
                # Not all movies we have in the database are in the tmdb database
                continue

            # Movie title + (year)
            movie_title = movie[1] + " (" + movie[2].strftime("%Y") + ")"
            # Convert date to string
            movie_date = movie[2].strftime("%d %B %Y")
            # Shorten synopsis
            synopsis = movie[3][:100] + "..."
            result += [(movie_title, movie_date, synopsis, poster, banner)]

    return result


def get_genre_pages(genre: str, limit: int = 30) -> dict[str, int]:
    """
    Get the number of pages
    :param genre: Genre name
    :type genre: str
    :param limit: Number of movies per page
    :type limit: int
    :return: total_pages, pages_left
    :rtype: dict[str, int]
    """
    stmt = "SELECT ceil(count(*) / ?), ceil(count(*) / ?) - ? " \
           "FROM Movie " \
           "INNER JOIN Movie_Genre " \
           "ON Movie.movie_id = Movie_Genre.movie_id " \
           "INNER JOIN Genre " \
           "ON Movie_Genre.genre_id = Genre.genre_id " \
           "WHERE Genre.name = ? " \
           "AND release_date <> '2045-05-31';"

    cursor.execute(stmt, (limit, limit, limit, genre))
    total_pages, pages_left = cursor.fetchone()
    return {"total_pages": total_pages, "pages_left": pages_left}


def get_all_genres() -> list[tuple]:
    """
    Returns a list of genres
    :return: List of genres (genre_id, name)
    :rtype: list[tuple]
    """
    stmt = "SELECT genre_id, name " \
           "FROM Genre;"

    cursor.execute(stmt)

    return cursor.fetchall()

def get_movie_by_id(id):
    stmt = "SELECT * FROM Movie WHERE movie_id = ?"
    cursor.execute(stmt, (id,))
    return cursor.fetchone()