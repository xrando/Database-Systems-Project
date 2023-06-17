import mariadb
import tmdbsimple as tmdb
import configparser
import os

config = configparser.ConfigParser()
config_route = os.path.join(os.path.dirname(__file__), '..', '..', 'Config', 'config.ini')

try:
    config.read(config_route)
except configparser.Error as e:
    print(f"Error reading config file: {e}")


def Movie_list(self, page: int = 1, limit: int = 30) -> list[tuple]:
    """
    Get all movies in the database, for the home page (30 most recent)

    Used to show movies in the home page.

    :param page: Page number (For Frontend)
    :type page: int
    :param limit: Number of movies per page
    :type limit: int
    :return: List of movies (title, release_date)
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
    self.cursor.execute(stmt, (limit, offset))
    movies = self.cursor.fetchall()
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

def get_movie_by_title(self, title: str) -> dict:
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
        self.cursor.execute(movie_stmt, (title,))
        movie = self.cursor.fetchone()
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

        self.cursor.execute(director_stmt, (title,))
        director = self.cursor.fetchone()

        director_tmdb_id = director[1]
        # director_name = director[0].replace(" ", "-")
        # director_link = config.get("MOVIE", "TMDB_PERSON_URL") + director_tmdb_id + "-" + director_name
        result["director"] = (director[0], director_tmdb_id)

        self.cursor.execute(actor_stmt, (title,))
        actors = self.cursor.fetchall()
        result["actors"] = list(actors)

        self.cursor.execute(genre_stmt, (title,))
        genres = self.cursor.fetchall()
        result["genres"] = [genre[0] for genre in genres]
    except mariadb.Error as e:
        print(f"Error executing statement: {e}")

    return result


def get_pages(self, pages: int = 1, limit: int = 30) -> dict[str, int]:
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

    self.cursor.execute(stmt, (limit, limit, pages))
    total_pages, pages_left = self.cursor.fetchone()
    return {"total_pages": total_pages, "pages_left": pages_left}


def carousel(self) -> list[tuple]:
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
        self.cursor.execute(stmt, (len(result) + current_offset,))
        movie = self.cursor.fetchone()
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
