#!/usr/bin/env python3

import mariadb
import sys
import tmdbsimple as tmdb
import configparser
import argparse
import os

config = configparser.ConfigParser()
config_route = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'Config', 'config.ini')

try:
    config.read(config_route)
except configparser.Error as e:
    print(f"Error reading config file: {e}")
    sys.exit(1)


class DBMS_Movie:
    raise NotImplementedError("Please implement this class")
    try:
        user = config.get('DBMS_MOVIE', 'USERNAME')
        password = config.get('DBMS_MOVIE', 'PASSWORD')
        host = config.get('DBMS_MOVIE', 'HOST')
        port = int(config.get('DBMS_MOVIE', 'PORT'))
        database = config.get('DBMS_MOVIE', 'DATABASE')
        tmdb.API_KEY = config.get('TMDB', 'API_KEY')
    except configparser.Error as e:
        print(f"Available Configurations: {config.sections()}")
        print(f"Error reading config file: {e}")
        sys.exit(1)

    if tmdb.API_KEY == "":
        raise ValueError("Please enter your TMDB API key in the config.ini file")

    def __init__(self) -> None:
        """
        Database Constructor, connects to the database and creates the tables if they do not exist

        All Configurations are stored in the config.ini file in path ../Config/config.ini
        """

        try:
            self.connection = mariadb.connect(
                user=self.user,
                password=self.password,
                host=self.host,
                port=self.port,
                database=self.database
            )

            self.cursor = self.connection.cursor()
        except mariadb.DatabaseError as e:
            # Try to create database
            try:
                self.connection = mariadb.connect(
                    user=self.user,
                    password=self.password,
                    host=self.host,
                    port=self.port
                )
                self.cursor = self.connection.cursor()
                self.cursor.execute("CREATE DATABASE IF NOT EXISTS " + self.database)
                self.cursor.execute("USE " + self.database)
                self.create_tables()
                self.seed()
            except mariadb.Error as e:
                print(f"Error connecting to MariaDB Platform: {e}")
                sys.exit(1)
        except mariadb.OperationalError as e:
            print(f"Error connecting to MariaDB Platform: {e}")
            sys.exit(1)

    def create_tables(self) -> None:
        """
        Database Migration Function, creates the tables in the database
        Schema of the database:

        Movie (movie_id, title, release_date, synopsis)

        Genre (genre_id, name)

        Movie_Genre (movie_id, genre_id)

        Actor (actor_id, actor_name, wiki_link)

        Director (director_id, director_name, wiki_link)

        Movie_Actor (movie_id, actor_id)

        Movie_Director (movie_id, director_id)

        :return: None
        """
        movie_table_file = "tables.sql"

        # Connect to the database
        try:
            self.cursor.execute("USE DBMS_Movie")
        except mariadb.Error as e:
            print(f"Error connecting to MariaDB Platform: {e}")
            sys.exit(1)

        # Open the table file
        with open(movie_table_file, 'r') as f:
            # Execute the table file
            try:
                self.cursor.execute(f.read())
            except mariadb.Error as e:
                print(f"Error executing table file: {e}")
                sys.exit(1)

    def seed(self, seed_file: str = None) -> None:
        """
        Seeds the database with the data from the seed_file

        :param seed_file: The file to seed the database with
        :type seed_file: str
        :return: None
        """
        import os
        import subprocess

        if seed_file is None:
            seed_file = "Seed.sql"
            print(f"[+] No seed file specified, using default seed file: {seed_file}")

        if not os.path.exists(seed_file):
            print(f"[-] Error: {seed_file} does not exist")
            return

        file_path = os.path.abspath(seed_file)

        try:
            command = f"mysql --database {self.database} -u {self.user} -p{self.password} < '{file_path}'"
            subprocess.run(command, shell=True, check=True)
        except subprocess.CalledProcessError as e:
            print(f"[-] Error seeding database\n {e}")
            return

        print("[+] Database seeded successfully")

        # Connect to the database
        try:
            self.cursor.execute("USE DBMS_Movie")
        except mariadb.Error as e:
            print(f"Error connecting to MariaDB Platform: {e}")
            sys.exit(1)

        # Open the seed file
        with open(seed_file, 'r') as f:
            # Execute the seed file
            try:
                self.cursor.execute(f.read())
            except mariadb.Error as e:
                print(f"Error executing seed file: {e}")
                sys.exit(1)
        # Commit the changes
        self.connection.commit()

    def get_movie(self, movie_id: int) -> tuple:
        self.cursor.execute("SELECT * FROM Movie WHERE movie_id = ?", (movie_id,))
        return self.cursor.fetchone()

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

    def Actor(self, actor_name: str = None, actor_tmdb_id: str = None, order_by=None) -> dict:
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
            self.cursor.execute(stmt, (actor_name or actor_tmdb_id,))
            movies = self.cursor.fetchall()
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
                self.cursor.execute(stmt, (actor_tmdb_id,))
                actor_name = self.cursor.fetchone()[0]
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
                self.cursor.execute(stmt, (actor_name,))
                actor_tmdb_id = self.cursor.fetchone()[0]
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

    def Director(
            self,
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
            self.cursor.execute(stmt, (director_name or director_tmdb_id,))
            movies = self.cursor.fetchall()
        except mariadb.Error as e:
            print(f"Error: {e}")
            return {"movies": [], "director": None}

        result = []
        for movie in movies:
            result += [(movie[0], movie[1].strftime("%B %d, %Y"))]

        director_info = None
        if director_tmdb_id:
            try:
                director_info = tmdb.People(director_tmdb_id).info()
            except IndexError:
                director_info = None
        elif director_name:
            stmt = "SELECT tmdb_id " \
                   "FROM Director " \
                   "WHERE director_name = ?"
            try:
                self.cursor.execute(stmt, (director_name,))
                director_tmdb_id = self.cursor.fetchone()[0]
            except [mariadb.Error, TypeError] as e:
                print(f"Error getting director's tmdb_id: {e}")

            if director_tmdb_id is not None:
                try:
                    director_info = tmdb.People(director_tmdb_id).info()
                except IndexError:
                    director_info = None
        else:
            raise ValueError("Either ONE director_name or director_tmdb_id must be specified")

        return {"movies": result, "director": director_info}

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

    # search
    def search_directors(self, name: str) -> tuple:
        self.cursor.execute("SELECT * "
                            "FROM director "
                            "WHERE director_name "
                            "LIKE %s"
                            "LIMIT 30", ('%' + name + '%',))
        return self.cursor.fetchall()

    def search_movies(self, name: str) -> tuple:
        self.cursor.execute("SELECT * "
                            "FROM movie "
                            "WHERE title "
                            "LIKE %s"
                            "LIMIT 30", ('%' + name + '%',))
        return self.cursor.fetchall()

    def search_actors(self, name: str) -> tuple:
        self.cursor.execute("SELECT * "
                            "FROM actor "
                            "WHERE actor_name "
                            "LIKE %s"
                            "LIMIT 30", ('%' + name + '%',))
        return self.cursor.fetchall()


def parse_args() -> None:
    import subprocess
    import os
    """
    Parse command line arguments
    -t, --table-create: Create tables in database (this uses the tables.sql file)
    -s, --seed: Seed database with data with SQL script
    :return: None
    """
    parser = argparse.ArgumentParser(
        description="Database Management System for Movie Database. "
                    "Ensure that you have a Config.ini file in the Config folder. "
                    "Refer to config.ini for an example.",
        prog="DBMS Movie"
    )

    parser.add_argument(
        "-m",
        "--migration",
        action="store_true",
        help="Run migration script (tables.sql)"
    )

    parser.add_argument(
        "-s",
        "--seed",
        action="store_true",
        help="Seed database with data (seed.sql) This will create tables if they do not exist"
    )

    args = parser.parse_args()

    # config = configparser.ConfigParser()
    # config.read('../../Config/config.ini')

    user = config.get('DBMS_MOVIE', 'USERNAME')
    password = config.get('DBMS_MOVIE', 'PASSWORD')
    host = config.get('DBMS_MOVIE', 'HOST')
    port = int(config.get('DBMS_MOVIE', 'PORT'))
    database = config.get('DBMS_MOVIE', 'DATABASE')
    try:
        connection = mariadb.connect(user=user, password=password, host=host, port=port)
        cursor = connection.cursor()
        # Create database if it does not exist
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {database};")
        cursor.execute(f"USE {database};")
    except mariadb.Error:
        print(f"[-] Error connecting to database\n {e}")
        return

    def migration() -> None:
        """
        Create tables in database
        :return: None
        """

        file = "tables.sql"
        if not os.path.exists(file):
            print(f"[-] Error: {file} does not exist")
            return

        file_path = os.path.abspath(file)

        try:
            command = f"mysql --database {database} -u {user} -p{password} --host {host} --port {port} < '{file_path}'"
            subprocess.run(command, shell=True, check=True)
        except subprocess.CalledProcessError as e:
            print(f"[-] Error creating tables\n {e}")
            return

        print("[+] Tables created successfully")

    def seed_database() -> None:
        """
        Seed database with data with sqldump
        :return: None
        """

        file = "Seed.sql"
        if not os.path.exists(file):
            print(f"[-] Error: {file} does not exist")
            return

        file_path = os.path.abspath(file)

        try:
            command = f"mysql --database {database} -u {user} -p{password} --host {host} --port {port} < '{file_path}'"
            subprocess.run(command, shell=True, check=True)
        except subprocess.CalledProcessError as e:
            print(f"[-] Error seeding database\n {e}")
            return

        print("[+] Database seeded successfully")

    action_map = {"migration": migration, "seed": seed_database}

    for action, func in action_map.items():
        if getattr(args, action):
            func()
            return
    else:
        parser.print_help()


def new_movie(title: str = None, tmdb_id: int = None) -> None:
    """
    Adds a new movie to the database

    Search for movie on tmdb api, need to update Director, Actor, Genre tables and their Movie_ tables
    :param title: Title of the movie
    :type title: str
    """

    movie_info = tmdb.Search().movie(query=title)['results'][0]
    movie_tmdb_id = movie_info['id']
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
    import requests

    url = "https://api.themoviedb.org/3/movie/" + str(movie_tmdb_id) + "/credits?language=en-US"

    headers = {
        "accept": "application/json",
        "Authorization": "Bearer " + config.get("TMDB", "ACCESS_TOKEN")
    }

    response = requests.get(url, headers=headers)

    from pprint import pprint

    cast_dict = {}
    for cast in response.json()['cast']:
        cast_dict[cast['name']] = [cast['id'], cast['character']]
    for crew in response.json()['crew']:
        if crew['job'] == 'Director':
            director = crew['name']
            director_id = crew['id']
            break

    pprint(cast_dict)
    print(director, director_id)

    # Insert to DB if not exists
    movie_stmt = "INSERT INTO Movie (title, release_date, synopsis) VALUES (?, ?, ?)" \
    cursor.execute(movie_stmt, (movie_title, movie_release_date, synopsis))
    movie_id = cursor.lastrowid

    for genre in movie_genres:
        genre_id = check_genre(genre)
        if genre_id is None:
            genre_stmt = "INSERT INTO Genre (name) VALUES (?)"
            cursor.execute(genre_stmt, (genre,))
            genre_id = check_genre(genre)
        movie_genre_stmt = "INSERT INTO Movie_Genre (movie_id, genre_id) VALUES (?, ?)"
        cursor.execute(movie_genre_stmt, (movie_id, genre_id))

    for actor in cast_dict:
        actor_id = check_actor(actor)
        if actor_id is None:
            actor_stmt = "INSERT INTO Actor (name) VALUES (?)"
            cursor.execute(actor_stmt, (actor,))
            actor_id = check_actor(actor)
        movie_actor_stmt = "INSERT INTO Movie_Actor (movie_id, actor_id, character) VALUES (?, ?, ?)"
        cursor.execute(movie_actor_stmt, (movie_id, actor_id, cast_dict[actor][1]))

    director_id = check_director(director)
    if director_id is None:
        director_stmt = "INSERT INTO Director (name) VALUES (?)"
        cursor.execute(director_stmt, (director,))
        director_id = check_director(director)
    movie_director_stmt = "INSERT INTO Movie_Director (movie_id, director_id) VALUES (?, ?)"
    cursor.execute(movie_director_stmt, (movie_id, director_id))

def check_genre(genre: str) -> int|None:
    genre_stmt = "SELECT id FROM Genre WHERE name = ?"
    genre_check = cursor.execute(genre_stmt, (genre,))

    if genre_check is not None:
        return genre_check
    else:
        return None

def check_actor(actor: str) -> int|None:
    actor_stmt = "SELECT id FROM Actor WHERE name = ?"
    actor_check = cursor.execute(actor_stmt, (actor,))

    if actor_check is not None:
        return actor_check
    else:
        return None

def check_director(director: str) -> int|None:
    director_stmt = "SELECT id FROM Director WHERE name = ?"
    director_check = cursor.execute(director_stmt, (director,))

    if director_check is not None:
        return director_check
    else:
        return None



if __name__ == "__main__":
    new_movie("Extraction 2")
