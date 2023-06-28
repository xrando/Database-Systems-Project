from typing import Tuple, Any, List

import mariadb
import tmdbsimple as tmdb
from .DB_Connect import DBConnection
from Config.ConfigManager import ConfigManager
import requests
import random
import Database.Mongo as Mongo
import concurrent.futures

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
            print("No movie found with the given title")
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
    Returns a list of 5 movies that are within 1 month of the current date and have a banner image
    :return: List of movies (title, release_date, banner)
    :rtype: list[tuple]
    """
    result = []
    desired_length = random.randint(5, 7)  # Randomly choose the number of movies to select

    stmt = "SELECT title, release_date " \
           "FROM Movie " \
           "WHERE release_date " \
           "BETWEEN CURRENT_DATE() - INTERVAL 1 MONTH " \
           "AND CURRENT_DATE() + INTERVAL 1 MONTH " \
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


def new_movie(title: str = None, tmdb_id: int = None) -> None:
    """
    Adds a new movie to the database

    Search for movie on tmdb api, need to update Director, Actor, Genre tables and their Movie_ tables
    :param tmdb_id: TMDB id of the movie
    :param title: Title of the movie
    :type title: str
    """

    director = None

    # Get movie info
    if title is not None:
        try:
            movie_info = tmdb.Search().movie(query=title)['results'][0]
            print(movie_info)
            movie_tmdb_id = movie_info['id']
            movie_title = movie_info['title']
            movie_release_date = movie_info['release_date']
            synopsis = movie_info['overview']
        except IndexError:
            print(f"Movie {title} not found on TMDB. Please try again.")
            return None
    elif tmdb_id is not None:
        movie_info = tmdb.Movies(tmdb_id).info()
        print('movie info: ' + movie_info)
        movie_tmdb_id = movie_info['id']
        print('movie id: ' + movie_tmdb_id)
        movie_title = movie_info['title']
        movie_release_date = movie_info['release_date']
        synopsis = movie_info['overview']

    # Get Genres
    movie_genres = []
    movie = tmdb.Movies(movie_tmdb_id)
    genres = movie.info()['genres']
    for genre in genres:
        movie_genres += [genre['name']]

    # Get Actors and Directors
    url = "https://api.themoviedb.org/3/movie/" + str(movie_tmdb_id) + "/credits?language=en-US"

    headers = {
        "accept": "application/json",
        "Authorization": "Bearer " + config.get("TMDB", "ACCESS_TOKEN")
    }

    response = requests.get(url, headers=headers)

    cast_dict = {}
    for cast in response.json()['cast']:
        cast_dict[cast['name']] = [cast['id'], cast['character']]
    for crew in response.json()['crew']:
        try:
            if crew['job'] == 'Director':
                director = crew['name']
                director_id = crew['id']
                break
        except KeyError:
            continue
    if director is not None and director_id is not None:
        try:
            # insert director into db
            director_stmt = "INSERT INTO Director (director_name,tmdb_id) VALUES (?, ?)"
            cursor.execute(director_stmt, (director, director_id))
            director_id = check_director(director)
            print('director id after insert: ' + str(director_id))
        except:
            print("Error inserting director into db")

    # Insert to DB if not exists
    movie = check_movie(movie_title)
    if movie is None:
        movie_stmt = "INSERT INTO Movie (title, release_date, synopsis) VALUES (?, ?, ?)"
        cursor.execute(movie_stmt, (movie_title, movie_release_date, synopsis))
        movie_id = cursor.lastrowid
        movie_id = int(movie_id)
        print(f"Movie {movie_title} added to database.")

        for genre in movie_genres:
            genre_id = check_genre(genre)
            if genre_id is None:
                genre_stmt = "INSERT INTO Genre (name) VALUES (?)"
                cursor.execute(genre_stmt, (genre,))
                genre_id = check_genre(genre)
            movie_genre_stmt = "INSERT INTO Movie_Genre (movie_id, genre_id) VALUES (?, ?)"
            cursor.execute(movie_genre_stmt, (movie_id, genre_id))
        print(f"Genres added to database.")

        if cast_dict is not None:
            for actor in cast_dict:
                actor_id = check_actor(actor)
                if actor_id is None:
                    actor_stmt = "INSERT INTO Actor (actor_name, tmdb_id) VALUES (?, ?)"
                    cursor.execute(actor_stmt, (actor, cast_dict[actor][0]))
                    actor_id = check_actor(actor)
                movie_actor_stmt = "INSERT INTO Movie_Actor (movie_id, actor_id, movie_character) VALUES (?, ?, ?)"
                cursor.execute(movie_actor_stmt, (movie_id, actor_id, str(cast_dict[actor][1])))
        print(f"Actors added to database.")
        if director is not None:
            director_id = check_director(director)
            print('director id is not none: ' + str(director_id))
            if director_id is None:
                director_stmt = "INSERT INTO Director (director_name,tmdb_id) VALUES (?, ?)"
                print('director: ' + director)
                print('director id: ' + str(director_id))
                cursor.execute(director_stmt, (director, director_id))
                director_id = check_director(director)
                print('director id after insert: ' + str(director_id))
            # problem here
            movie_director_stmt = "INSERT INTO Movie_Director (movie_id, director_id) VALUES (?, ?)"
            cursor.execute(movie_director_stmt, (movie_id, director_id))
        else:
            # add blank to directors
            pass
        print(f"Director added to database.")
    else:
        print(f"Movie {movie_title} already exists in database.")


def check_genre(genre: str) -> int | None:
    genre_stmt = "SELECT genre_id FROM Genre WHERE name LIKE ?"
    cursor.execute(genre_stmt, (genre,))
    id = cursor.fetchone()
    if id is None:
        return None
    return id[0]


def check_actor(actor: str) -> int | None:
    actor_stmt = "SELECT actor_id FROM Actor WHERE actor_name LIKE ?"
    cursor.execute(actor_stmt, (actor,))
    id = cursor.fetchone()
    if id is None:
        return None
    return id[0]


def check_director(director: str) -> int | None:
    director_stmt = "SELECT director_id FROM Director WHERE director_name LIKE ?"
    cursor.execute(director_stmt, (director,))
    id = cursor.fetchone()
    if id is None:
        return None
    return id[0]


def check_movie(movie: str) -> int | None:
    movie_stmt = "SELECT movie_id FROM Movie WHERE title LIKE ?"
    cursor.execute(movie_stmt, (movie,))
    id = cursor.fetchone()
    if id is None:
        return None
    return id[0]


def get_movie_info(movie: str) -> Tuple[Any, Any, Any, List[Any]]:
    """
    Gets movie info from TMDB API, and returns movie info (tmdb_id: int, Poster: str, Banner: str, Rating: list[float, int])

    Data is cached in MongoDB, and will be retrieved from there if available.
    :param movie: Movie Title to search for
    :return: None if movie not found, else returns movie info (Poster: str, Banner: str, Rating: list[float, int])
    """
    poster_link = config.get('MOVIE', 'TMDB_IMAGE_URL')
    poster = None
    banner = None
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
                else:
                    poster = None
                if movie_info['backdrop_path'] is not None:
                    banner = poster_link + movie_info['backdrop_path']
                else:
                    banner = None
                try:
                    rating = [movie_info['vote_average'], movie_info['vote_count']]
                except KeyError:
                    rating = None
            else:
                poster = None
                banner = None
        except TypeError:
            # Not all movies we have in the database are in the tmdb database
            poster = None
            banner = None
        except IndexError:
            # Not all movies we have in the database are in the tmdb database
            poster = None
            banner = None

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


def movie_recommendation(user_id: int, limit: int = 6) -> list[tuple[str, str]]:
    """
    Get random movies based on the movie genres the user has watched
    :param limit: Number of movies to return
    :param user_id: User ID
    :return: List of movies (title, poster_link)
    """

    # Get user's watched movies from MongoDB "watchlist" collection
    watched_movies_document = handler.find_documents(config.get('MONGODB', 'WATCHLIST_COLLECTION'), {'user_id': user_id})
    if len(watched_movies_document) != 0:
        watched_movies = watched_movies_document[0]['watchlist_arr']

        # Get user's watched movie genres and find the most common genre
        genres = {}
        for movie in watched_movies:
            # Get the movie's genre_id based on movie_id, from Movie_Genre table
            current_movie_genre = get_genre(int(movie))
            if current_movie_genre is not None:
                genres[current_movie_genre] = genres.get(current_movie_genre, 0) + 1

        if genres:
            # Get the most common genre
            most_common_genre = max(genres, key=genres.get)

            # Get random movies from the most common genre within +-1 year of the current date
            stmt = "SELECT Movie.title " \
                   "FROM Movie " \
                   "INNER JOIN Movie_Genre ON Movie.movie_id = Movie_Genre.movie_id " \
                   "WHERE Movie_Genre.genre_id = ? " \
                   "AND Movie.release_date BETWEEN DATE_SUB(NOW(), INTERVAL 1 YEAR) AND DATE_ADD(NOW(), INTERVAL 1 YEAR) " \
                   "ORDER BY RAND() " \
                   "LIMIT ?"

            cursor.execute(stmt, (most_common_genre, limit))
            movies = cursor.fetchall()

            result = []
            movie_info_list = []

            with concurrent.futures.ThreadPoolExecutor() as executor:
                # Collect movie information concurrently
                for movie in movies:
                    movie_title = movie[0]
                    future = executor.submit(get_movie_info, movie_title)
                    movie_info_list.append((movie_title, future))

                for movie_title, future in movie_info_list:
                    try:
                        movie_id, poster, banner, rating = future.result()
                        if poster is None:
                            poster = config.get("MOVIE", "DEFAULT_POSTER_URL")
                        result.append((movie_title, poster))
                    except Exception as e:
                        # Handle any exceptions that occurred during movie information retrieval
                        print(f"Error occurred while fetching movie info for '{movie_title}': {str(e)}")

            return result

    return []


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
