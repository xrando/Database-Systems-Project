####################################################################################################
# These are the functions for the all Movie-based pages.                                           #
# Data collection is mostly multithreaded to improve performance.                                  #
# The functions are organized by page.                                                             #
####################################################################################################

import concurrent.futures
import logging
import random
from collections import Counter
from typing import Optional, Any

import mariadb
import requests
import tmdbsimple as tmdb

import Database.Mongo as Mongo
from Config.ConfigManager import ConfigManager
from .DB_Connect import DBConnection

# Initialize the config manager
config_manager = ConfigManager()

# Get the configuration
config = config_manager.get_config()

tmdb.API_KEY = config.get('TMDB', 'API_KEY')

connection = DBConnection().connection
cursor = connection.cursor()

handler = Mongo.MongoDBHandler.get_instance(
    config.get('MONGODB', 'CONNECTION_STRING'),
    config.get('MONGODB', 'DATABASE')
)


def Movie_list(page: int = 1, limit: int = 30) -> list[tuple]:
    """
    Get all movies in the database, for the home page (30 most recent)

    Used to show movies on the home page.

    :param page: Page number (For Frontend)
    :type page: int
    :param limit: Number of movies per page
    :type limit: int
    :return: List of movies (title, release_date, synopsis, poster_link, banner_link)
    :rtype: list[tuple]
    """
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

    # Helper function to get movie info concurrently
    def get_movie_info_concurrent(movie):
        tmdb_id, poster, banner, rating = get_movie_info(movie[0])
        if poster is None:
            poster = config.get("MOVIE", "DEFAULT_POSTER_URL")
        if banner is None:
            banner = config.get("MOVIE", "DEFAULT_BANNER_URL")
        movie_title = movie[0] + " (" + movie[1].strftime("%Y") + ")"
        movie_date = movie[1].strftime("%d %B %Y")
        synopsis = movie[2][:100] + "..."
        return (movie_title, movie_date, synopsis, poster, banner)

    # Execute get_movie_info concurrently
    with concurrent.futures.ThreadPoolExecutor() as executor:
        movie_info_results = executor.map(get_movie_info_concurrent, movies)

    # Collect the results
    result = list(movie_info_results)

    return result


def movie_page(title: str) -> dict | None:
    """
    Get a movie by title as a dictionary of the following format:

    result: {
            "title": str, "release_date": str, "synopsis": str, "movie_id": int,
            "director": {"director_name": str, "tmdb_id": int},
            "actors": [(name: str, tmdb_id: int, character: str), ...],
            "genres": [genre: str, ...],
            "movie": (title: str, release_date: str, synopsis: str, poster: str, banner: str, movie_id: int),
            "rating": [rating: float, count: int],
            "tmdb_link": str
            }

    Used for the movie page to display all the information about a movie

    :param title: Movie title
    :return: Movie dictionary
    :rtype: dict
    """
    result = {}

    movie_query = "SELECT Movie.title, Movie.release_date, Movie.synopsis, Movie.movie_id, " \
                  "Director.director_name, Director.tmdb_id, " \
                  "Actor.actor_name, Actor.tmdb_id, Movie_Actor.movie_character, " \
                  "Genre.name " \
                  "FROM Movie " \
                  "JOIN Movie_Director ON Movie.movie_id = Movie_Director.movie_id " \
                  "JOIN Director ON Movie_Director.director_id = Director.director_id " \
                  "JOIN Movie_Actor ON Movie.movie_id = Movie_Actor.movie_id " \
                  "JOIN Actor ON Movie_Actor.actor_id = Actor.actor_id " \
                  "JOIN Movie_Genre ON Movie.movie_id = Movie_Genre.movie_id " \
                  "JOIN Genre ON Movie_Genre.genre_id = Genre.genre_id " \
                  "WHERE Movie.title = ?"

    try:
        cursor.execute(movie_query, (title,))
        rows = cursor.fetchall()

        if rows:
            movie = rows[0]
            movie_date = movie[1].strftime("%d %B %Y")
            movie_id, poster, banner, rating = get_movie_info(movie[0])

            result["movie"] = (movie[0], movie_date, movie[2], poster, banner, movie[3])
            result["rating"] = rating
            result["director"] = (movie[4], movie[5])

            genres = {row[9] for row in rows}
            result["genres"] = list(genres)

            actors = {(row[6], row[7], row[8]) for row in rows}
            result["actors"] = list(actors)

            result["tmdb_link"] = config.get("MOVIE", "TMDB_MOVIE_URL") + str(movie_id)
        else:
            logging.error(f"No movie found with the given title: {title}")
    except mariadb.Error as e:
        logging.error(f"Error executing statement: {e}")

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
    Returns a list of 5 movies that are within 1 year of the current date and have a banner image
    :return: List of movies (title, release_date, banner)
    :rtype: list[tuple]
    """
    result = []
    desired_length = random.randint(5, 7)  # Randomly choose the number of movies to select

    stmt = "SELECT title, release_date " \
           "FROM Movie " \
           "WHERE release_date " \
           "BETWEEN CURRENT_DATE() - INTERVAL 1 YEAR " \
           "AND CURRENT_DATE() + INTERVAL 1 YEAR " \
           "ORDER BY RAND() " \
           "LIMIT ?;"

    cursor.execute(stmt, (desired_length,))
    movies = cursor.fetchall()

    # Helper function to get banner image concurrently
    def get_banner_concurrent(movie):
        banner = get_movie_info(movie[0])[2]
        if banner is not None:
            movie_date = movie[1].strftime("%d %B %Y")
            return movie[0], movie_date, banner
        else:
            return None

    # Execute get_banner_concurrent concurrently
    with concurrent.futures.ThreadPoolExecutor() as executor:
        banner_results = executor.map(get_banner_concurrent, movies)

    # Collect the results
    for banner_result in banner_results:
        if banner_result is not None:
            result.append(banner_result)
        if len(result) == desired_length:
            break

    return result


def Genre(genre: str = None, page: int = 1, limit: int = 30) -> list[tuple]:
    """
    Returns a list of Movies based on the genre
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
        result = []

        # Helper function to get movie info concurrently
        def get_movie_info_concurrent(movie):
            movie_id, poster, banner, ratings = get_movie_info(movie[1])
            if poster is None:
                poster = config.get("MOVIE", "DEFAULT_POSTER_URL")
            if banner is None:
                banner = config.get("MOVIE", "DEFAULT_BANNER_URL")
            movie_title = movie[1] + " (" + movie[2].strftime("%Y") + ")"
            movie_date = movie[2].strftime("%d %B %Y")
            synopsis = movie[3][:100] + "..."
            return movie_title, movie_date, synopsis, poster, banner

        # Execute get_movie_info concurrently
        with concurrent.futures.ThreadPoolExecutor() as executor:
            movie_info_results = executor.map(get_movie_info_concurrent, movies)

        # Collect the results
        result = list(movie_info_results)

    return result


def get_genre_pages(genre: str, limit: int = 30) -> dict[str, int]:
    """
    Get the number of pages for a genre
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


def new_movie(title: Optional[str] = None, tmdb_id: Optional[int] = None) -> bool:
    """
    Adds a new movie to the database

    Search for movie on TMDB API, need to update Director, Actor, Genre tables and their Movie_ tables
    :param tmdb_id: TMDB id of the movie
    :param title: Title of the movie
    :return: True if the movie was successfully added, False otherwise
    """

    director = None

    # Get movie info
    if title is not None:
        try:
            movie_info = tmdb.Search().movie(query=title)['results'][0]
            movie_tmdb_id = movie_info['id']
            movie_title = movie_info['title']
            movie_release_date = movie_info['release_date']
            synopsis = movie_info['overview']
            logging.info(movie_info)
        except IndexError:
            logging.error(f"Movie {title} not found on TMDB. Please try again.")
            return False
    elif tmdb_id is not None:
        try:
            movie_info = tmdb.Movies(tmdb_id).info()
            movie_tmdb_id = movie_info['id']
            movie_title = movie_info['title']
            movie_release_date = movie_info['release_date']
            synopsis = movie_info['overview']
        except requests.exceptions.HTTPError:
            logging.error(f"Movie with TMDB id {tmdb_id} not found on TMDB. Please try again.")
    else:
        logging.error("Invalid arguments. Please provide either 'title' or 'tmdb_id'.")
        return False

    try:
        with connection.cursor() as cursor:
            logging.info(f"Adding movie {movie_title} to database...")
            # Begin the transaction
            connection.begin()

            # Get Genres
            movie = tmdb.Movies(movie_tmdb_id)
            genres = movie.info().get('genres', [])
            movie_genres = [genre['name'] for genre in genres]

            # Get Actors and Directors
            url = f"https://api.themoviedb.org/3/movie/{movie_tmdb_id}/credits?language=en-US"
            headers = {
                "accept": "application/json",
                "Authorization": "Bearer " + config.get("TMDB", "ACCESS_TOKEN")
            }
            response = requests.get(url, headers=headers)
            cast_dict = {}

            for cast in response.json().get('cast', []):
                cast_dict[cast['name']] = [cast['id'], cast['character']]

            for crew in response.json().get('crew', []):
                if crew.get('job') == 'Director':
                    director = crew['name']
                    director_id = crew['id']
                    break

            # Insert director into DB if not None
            if director is not None and director_id is not None:
                director_stmt = "INSERT INTO Director (director_name, tmdb_id) VALUES (?, ?)"
                cursor.execute(director_stmt, (director, director_id))
                director_id = check_director(director)
                logging.info(f"Director added to database. Director ID: {director_id}")

            # Insert movie into DB if not exists
            movie = check_movie(movie_title)
            if movie is None:
                movie_stmt = "INSERT INTO Movie (title, release_date, synopsis) VALUES (?, ?, ?)"
                cursor.execute(movie_stmt, (movie_title, movie_release_date, synopsis))
                movie_id = cursor.lastrowid
                logging.info(f"Movie {movie_title} added to database. Movie ID: {movie_id}")

                for genre in movie_genres:
                    genre_id = check_genre(genre)
                    if genre_id is None:
                        genre_stmt = "INSERT INTO Genre (name) VALUES (?)"
                        cursor.execute(genre_stmt, (genre,))
                        genre_id = check_genre(genre)

                    movie_genre_stmt = "INSERT INTO Movie_Genre (movie_id, genre_id) VALUES (?, ?)"
                    cursor.execute(movie_genre_stmt, (movie_id, genre_id))

                logging.info("Genres added to the database.")

                for actor in cast_dict:
                    actor_id = check_actor(actor)
                    if actor_id is None:
                        actor_stmt = "INSERT INTO Actor (actor_name, tmdb_id) VALUES (?, ?)"
                        cursor.execute(actor_stmt, (actor, cast_dict[actor][0]))
                        actor_id = check_actor(actor)

                    movie_actor_stmt = "INSERT INTO Movie_Actor (movie_id, actor_id, movie_character) VALUES (?, ?, ?)"
                    cursor.execute(movie_actor_stmt, (movie_id, actor_id, str(cast_dict[actor][1])))

                logging.info("Actors added to the database.")

                if director is not None:
                    director_id = check_director(director)
                    if director_id is None:
                        director_stmt = "INSERT INTO Director (director_name, tmdb_id) VALUES (?, ?)"
                        cursor.execute(director_stmt, (director, director_id))
                        director_id = check_director(director)

                    movie_director_stmt = "INSERT INTO Movie_Director (movie_id, director_id) VALUES (?, ?)"
                    cursor.execute(movie_director_stmt, (movie_id, director_id))
            else:
                logging.info(f"Movie {movie_title} already exists in the database.")

            # Commit the transaction
            connection.commit()
            logging.info("Transaction committed.")
            return True
    except requests.exceptions.HTTPError as e:
        logging.error("HTTP error occurred while making TMDB API request:", e)
        # Rollback the transaction in case of an error
        connection.rollback()
        return False
    except Exception as e:
        logging.error("Error occurred in new_movie function:", e)
        # Rollback the transaction in case of an error
        connection.rollback()
        return False


def check_genre(genre: str) -> int | None:
    """
    Checks if genre exists in database
    :param genre: genre to check
    :type genre: str
    :return: genre id if exists, None otherwise
    """

    genre_stmt = "SELECT genre_id FROM Genre WHERE name LIKE ?"
    cursor.execute(genre_stmt, (genre,))
    id = cursor.fetchone()
    if id is None:
        return None
    return id[0]


def check_actor(actor: str) -> int | None:
    """
    Checks if actor exists in database
    :param actor: actor to check
    :type actor: str
    :return: actor id if exists, None otherwise
    :rtype: int | None
    """

    actor_stmt = "SELECT actor_id FROM Actor WHERE actor_name LIKE ?"
    cursor.execute(actor_stmt, (actor,))
    id = cursor.fetchone()
    if id is None:
        return None
    return id[0]


def check_director(director: str) -> int | None:
    """
    Checks if director exists in database
    :param director: director to check
    :type director: str
    :return: director id if exists, None otherwise
    :rtype: int | None
    """
    director_stmt = "SELECT director_id FROM Director WHERE director_name LIKE ?"
    cursor.execute(director_stmt, (director,))
    id = cursor.fetchone()
    if id is None:
        return None
    return id[0]


def check_movie(movie: str) -> int | None:
    """
    Checks if movie exists in database
    :param movie: movie to check
    :type movie: str
    :return: movie id if exists, None otherwise
    :rtype: int | None
    """
    movie_stmt = "SELECT movie_id FROM Movie WHERE title LIKE ?"
    cursor.execute(movie_stmt, (movie,))
    id = cursor.fetchone()
    if id is None:
        return None
    return id[0]


def get_movie_info(movie: str) -> tuple[Any | None, Any | None, Any | None, list[Any] | None | Any]:
    """
    Gets movie info from TMDB API, and returns movie info (tmdb_id: int, Poster: str, Banner: str, Rating: list[float, int])

    Data is cached in MongoDB, and will be retrieved from there if available.
    :param movie: Movie Title to search for
    :return: None if movie not found, else returns movie info (Poster: str, Banner: str, Rating: list[float, int])
    """
    poster_link = config.get('MOVIE', 'TMDB_IMAGE_URL')
    poster = config.get('MOVIE', 'DEFAULT_POSTER_URL')
    banner = config.get('MOVIE', 'DEFAULT_BANNER_URL')
    rating = None
    movie_id = None

    # Check if movie is in MongoDB cache
    data = handler.find_documents(config.get('MONGODB', 'MOVIE_INFO_COLLECTION'), {'title': movie})
    if len(data) > 0:
        movie_info = data[0]
        if movie_info['poster'] is not None:
            poster = movie_info['poster']
        if movie_info['banner'] is not None:
            banner = movie_info['banner']
        if movie_info['rating'] is not None:
            rating = movie_info['rating']
        if movie_info['tmdb_id'] is not None:
            movie_id = movie_info['tmdb_id']
    # If not in MongoDB cache, check TMDB
    else:
        try:
            movie_id = tmdb.Search().movie(query=movie)['results'][0]['id']
            movie_info = tmdb.Movies(movie_id).info()

            if movie_info is not None:
                if movie_info['poster_path'] is not None:
                    poster = poster_link + movie_info['poster_path']
                if movie_info['backdrop_path'] is not None:
                    banner = poster_link + movie_info['backdrop_path']
                try:
                    rating = [movie_info['vote_average'], movie_info['vote_count']]
                except KeyError:
                    rating = None
        except (TypeError, IndexError):
            # Not all movies we have in the database are in the tmdb database
            logging.warning(f"Movie {movie} not found in TMDB database.")

        # Add movie info to MongoDB cache
        handler.insert_document(config.get('MONGODB', 'MOVIE_INFO_COLLECTION'), {
            'tmdb_id': movie_id,
            'title': movie,
            'poster': poster,
            'banner': banner,
            'rating': rating
        }, True)

    return movie_id, poster, banner, rating


def movie_providers(tmdb_id: int) -> dict:
    """
    Get movie providers from TMDB API

    Data is cached in MongoDB
    :param tmdb_id: TMDB ID of movie
    :return: Dictionary of providers
    """

    data = handler.find_documents(
        config.get('MONGODB', 'MOVIE_PROVIDER_COLLECTION'),
        {'movie_tmdb_id': tmdb_id}
    )

    if data is not None and len(data) > 0:
        return data[0]['providers']
    else:
        url = f"https://api.themoviedb.org/3/movie/{tmdb_id}/watch/providers"

        headers = {
            "accept": "application/json",
            "Authorization": "Bearer " + config.get("TMDB", "ACCESS_TOKEN")
        }

        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            if 'US' in response.json()['results']:
                providers = response.json()['results']['US']
                handler.insert_document(config.get('MONGODB', 'MOVIE_PROVIDER_COLLECTION'),
                                        {'movie_tmdb_id': tmdb_id, 'providers': providers}, True)
                # Return inserted data
                return providers


def movie_recommendation(user_id: int = None, limit: int = 6) -> list[tuple[str, str]]:
    """
    Get random movies based on the movie genres the user has watched, with additional recommendations.

    SQL Statement will grab movies that have the same genre as the user's watched movies, and then
    randomly select a movie from that list. If the list is empty, then it will grab a random movie
    from the database.
    :param user_id: User ID
    :param limit: Number of movies to return
    :return: List of movies (title, poster_link)
    """

    def get_movie_info_concurrently(movies):
        result = []
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = [executor.submit(get_movie_info, movie[0]) for movie in movies]

            for movie, future in zip(movies, futures):
                movie_title = movie[0]
                try:
                    movie_id, poster, banner, rating = future.result()
                    if poster is None:
                        poster = config.get("MOVIE", "DEFAULT_POSTER_URL")
                    result.append((movie_title, poster))
                except Exception as e:
                    logging.error(f"Error occurred while fetching movie info for '{movie_title}': {str(e)}")
        return result

    # Get user's watched movies and their genres from MongoDB "watchlist" collection
    watched_movies_document = handler.find_documents(config.get('MONGODB', 'WATCHLIST_COLLECTION'),
                                                     {'user_id': user_id})
    watched_movies = watched_movies_document[0].get('watchlist_arr', []) if watched_movies_document else []

    genres = Counter(get_genre(int(movie)) for movie in watched_movies if get_genre(int(movie)))

    if genres:
        most_common_genre = genres.most_common(1)[0][0]

        # Create a read-only transaction
        cursor.execute("START TRANSACTION READ ONLY")

        # Get random movies from the most common genre within +-1 year of the current date,
        # including movies from the current year
        stmt = "SELECT DISTINCT Movie.title " \
               "FROM Movie " \
               "LEFT JOIN Movie_Genre " \
               "ON Movie.movie_id = Movie_Genre.movie_id " \
               "LEFT JOIN Movie_Director " \
               "ON Movie.movie_id = Movie_Director.movie_id " \
               "LEFT JOIN Movie_Actor " \
               "ON Movie.movie_id = Movie_Actor.movie_id " \
               "WHERE Movie_Genre.genre_id = ? " \
               "AND (Movie.release_date " \
               "BETWEEN DATE_SUB(NOW(), INTERVAL 1 YEAR) " \
               "AND DATE_ADD(NOW(), INTERVAL 1 YEAR) " \
               "OR YEAR(Movie.release_date) = YEAR(NOW())) " \
               "AND Movie.movie_id NOT IN (" + ",".join(["?"] * len(watched_movies)) + ") " \
                                                                                       "ORDER BY RAND() " \
                                                                                       "LIMIT ?"

        cursor.execute(stmt, (most_common_genre, *watched_movies, limit))
        movies = cursor.fetchall()

        result = get_movie_info_concurrently(movies)
        return result

        # Create a read-only transaction
    cursor.execute("START TRANSACTION READ ONLY")

    # Return random movies if no genres are found or no movies match the criteria in 1 year range
    stmt = "SELECT title " \
           "FROM Movie " \
           "WHERE release_date BETWEEN DATE_SUB(NOW(), INTERVAL 1 YEAR) AND DATE_ADD(NOW(), INTERVAL 1 YEAR) " \
           "ORDER BY RAND() " \
           "LIMIT ?"
    cursor.execute(stmt, (*watched_movies, limit))
    movies = cursor.fetchall()

    result = get_movie_info_concurrently(movies)
    return result


def get_genre(movie_id: int) -> int | None:
    """
    Get genre of movie from DB (Movie_Genre table)
    :param movie_id: TMDB ID of movie
    :return: Genre of movie
    """
    stmt = "SELECT genre_id FROM Movie_Genre WHERE movie_id = ?"
    cursor.execute(stmt, (movie_id,))
    genre = cursor.fetchone()
    if genre is None:
        return None
    return genre[0]


def get_genre_name(genre_id: int) -> int | None:
    """
    Get genre of movie from DB (Movie_Genre table)
    :param genre_id: Genre ID
    :return: Genre name of genre id
    """
    stmt = "SELECT name FROM Genre WHERE genre_id = ?"
    cursor.execute(stmt, (genre_id,))
    genre = cursor.fetchone()
    if genre is None:
        return None
    return genre[0]
