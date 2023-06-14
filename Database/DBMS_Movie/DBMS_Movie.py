import mariadb
import sys
import pandas as pd
import tmdbsimple as tmdb
import configparser
import concurrent.futures
import math
import requests
import argparse


class DBMS_Movie:

    def __init__(self) -> None:
        """
        Database Constructor, connects to the database and creates the tables if they do not exist

        All Configurations are stored in the config.ini file in path ../Config/config.ini
        """
        config = configparser.ConfigParser()
        config.read('../Config/config.ini')

        user = config.get('DBMS_MOVIE', 'USERNAME')
        password = config.get('DBMS_MOVIE', 'PASSWORD')
        host = config.get('DBMS_MOVIE', 'HOST')
        port = int(config.get('DBMS_MOVIE', 'PORT'))
        database = config.get('DBMS_MOVIE', 'DATABASE')
        tmdb.API_KEY = config.get('TMDB', 'API_KEY')

        if tmdb.API_KEY == "":
            raise ValueError("Please enter your TMDB API key in the config.ini file")

        try:
            self.connection = mariadb.connect(user=user, password=password, host=host, port=port, database=database)

            self.cursor = self.connection.cursor()
        except mariadb.DatabaseError as e:
            # Try to create database
            try:
                self.connection = mariadb.connect(user=user, password=password, host=host, port=port)
                self.cursor = self.connection.cursor()
                self.cursor.execute("CREATE DATABASE " + database)
                self.cursor.execute("USE " + database)
                self.create_tables()
                self.seed()
            except mariadb.Error as e:
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
        if seed_file is None:
            raise ValueError("Please provide a seed file (seed_file='path/to/file.sql')")

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
        Get a movie by title (movie, director, actors, genres)
        :param title: Movie title
        :return: Movie dictionary
        :rtype: dict
        """
        result = {}
        poster_link = "https://image.tmdb.org/t/p/original"

        movie_stmt = "Select Movie.title as movie_title, Movie.release_date, Movie.synopsis FROM Movie WHERE Movie.title = ?"
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

            result["movie"] = (movie[0], movie_date, movie[2], poster, banner)

            self.cursor.execute(director_stmt, (title,))
            director = self.cursor.fetchone()

            # TODO: Show this in director page instead
            director_tmdb_id = director[1]
            director_name = director[0].replace(" ", "-")
            director_link = "https://www.themoviedb.org/person/" + director_tmdb_id + "-" + director_name
            result["director"] = (director[0], director_link)

            # TODO: This gotta be in the actor page instead
            self.cursor.execute(actor_stmt, (title,))
            actors = self.cursor.fetchall()
            actor_results = []
            for actor in actors:
                actor_tmdb_id = actor[1]
                actor_name = actor[0].replace(" ", "-")
                actor_link = "https://www.themoviedb.org/person/" + actor_tmdb_id + "-" + actor_name
                # Replace actor[1] with link
                actor = (actor[0], actor_link, actor[2])
                actor_results.append(actor)
            result["actors"] = actor_results

            self.cursor.execute(genre_stmt, (title,))
            genres = self.cursor.fetchall()
            result["genres"] = [genre[0] for genre in genres]
        except mariadb.Error as e:
            print(f"Error executing statement: {e}")
            sys.exit(1)

        return result

    def Actor(self, actor_name: str = None, actor_tmdb_id: str = None, order_by=None) -> list[tuple]:
        """
        Get All movies an actor has been in, and their roles
        :param actor_name: Actor's name
        :type actor_name: str
        :param actor_tmdb_id: Actor's tmdb id
        :type actor_tmdb_id: str
        :param order_by: Order by release_date or title, ASC or DESC
        :type order_by: list
        :return: List of movies (title, release_date, movie_character)
        :rtype: List[tuple]
        """
        if order_by is None:
            order_by = ["release_date", "DESC"]
        orders = {"release_date": "release_date", "title": "title", "movie_id": "movie_id"}
        if order_by[0] not in orders:
            raise ValueError("order_by must be one of: release_date, title")

        movies = []
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

        stmt += "ORDER BY ? ?"

        try:
            self.cursor.execute(stmt, (actor_name or actor_tmdb_id, orders[order_by[0]], order_by[1]))
            movies = self.cursor.fetchall()
        except mariadb.Error as e:
            print(f"Error getting movies: {e}")
            sys.exit(1)
        result = []
        for movie in movies:
            result += [(movie[0], movie[1].strftime("%B %d, %Y"), movie[2])]

        return result

    def Director(self, director_name: str = None, director_tmdb_id: str = None, order_by=None) -> list[tuple]:
        """
        Get all movies a director has directed
        :param director_name: Director's name
        :type director_name: str
        :param director_tmdb_id: Director's tmdb_id
        :type director_tmdb_id: str
        :param order_by: Order by release_date or title, ASC or DESC
        :type order_by: list
        :return: List of movies (title, release_date)
        :rtype: List[tuple]
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

        stmt += "ORDER BY ? ?"
        try:
            self.cursor.execute(stmt, (director_name or director_tmdb_id, orders[order_by[0]], order_by[1]))
            movies = self.cursor.fetchall()
        except mariadb.Error as e:
            print(f"Error: {e}")
            return []

        result = []
        for movie in movies:
            result += [(movie[0], movie[1].strftime("%B %d, %Y"))]

        return result

    def Movie_list(self, page: int = 1, limit: int = 30) -> list[tuple]:
        """
        Get all movies in the database, for the home page (30 most recent)

        :param page: Page number (For Frontend)
        :type page: int
        :param limit: Number of movies per page
        :type limit: int
        :return: List of movies (title, release_date)
        :rtype: list[tuple]
        """
        poster_link = "https://image.tmdb.org/t/p/original"
        result = []
        offset = (page - 1) * limit

        stmt = "SELECT title, release_date " \
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
                continue

            # Convert date to string
            movie_date = movie[1].strftime("%d %B %Y")
            result += [(movie[0], movie_date, poster, banner)]

        return result

    def get_pages_left(self, pages: int = 1, limit: int = 30) -> int:
        """
        Get the number of pages left
        :param pages: Number of pages
        :type pages: int
        :param limit: Number of movies per page
        :type limit: int
        :return: Number of pages left
        :rtype: int
        """
        stmt = "SELECT COUNT(*) " \
               "FROM Movie " \
               "WHERE release_date < CURRENT_DATE();"
        self.cursor.execute(stmt)
        total_movies = self.cursor.fetchone()[0]
        return math.ceil(total_movies / limit) - pages

    def carousel(self) -> list[tuple]:
        """
        Returns a list of 5 movies that are within 1 month of current date and have a banner image
        :return: List of movies (title, release_date, banner)
        :rtype: list[tuple]
        """
        poster_link = "https://image.tmdb.org/t/p/original"
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


def get_genre_id(self, genre_name: str) -> int:
    try:
        self.cursor.execute("SELECT genre_id FROM Genre WHERE name LIKE ?", (genre_name,))
        return self.cursor.fetchone()[0]
    except mariadb.DataError as e:
        # Genre does not exist
        pass


def get_release_date(self, movie: str) -> str:
    try:
        self.cursor.execute("SELECT release_date FROM Movie WHERE title LIKE ?", (movie,))
        return self.cursor.fetchone()[0].strftime("%B %d, %Y")
    except mariadb.DataError as e:
        # Movie does not exist
        pass


def run(self, stmt: str, args: tuple = ()) -> tuple:
    """
    Run a SQL statement and return the result
    :param stmt: SQL statement to run
    :type stmt: str
    :param args: Arguments to pass to the SQL statement
    :type args: tuple
    :return: Result of the SQL statement
    """
    self.cursor.execute(stmt, args)
    return self.cursor.fetchall()


# Data Collection Functions (Do not use in production)

def populate_with_csv(self) -> None:
    raise NotImplementedError
    # Open the CSV file and read it into a pandas dataframe
    df = pd.read_csv(self.dataset)
    error_array = []

    # Insert first 3 columns into Movie table (id, title, synopsis), release data is the current date
    def process_movie(row):
        print(f"Inserting : {row['title'], row['overview']}")
        # Check if title is already in the database
        self.cursor.execute("SELECT title FROM Movie WHERE title = ?", (row["title"],))
        if self.cursor.fetchone() is not None:
            return
        release_date = self.get_release_date(row["title"]) or "2045-05-31"
        try:
            self.cursor.execute("INSERT INTO Movie (title, release_date, synopsis) VALUES (?, ?, ?)",
                                (row["title"], release_date, row["overview"]))
            self.connection.commit()
            self.populate_genres(row["title"])
        except mariadb.DataError as e:
            # Insert title into error array
            error_array.append(row["title"])
        except mariadb.Error as e:
            with open("error_log.txt", "a") as error_log:
                error_log.write(f"Error inserting {row['title']}: {e}\n")

    num_rows = len(df)
    num_threads = 4  # Define the number of threads you want to use
    chunk_size = math.ceil(num_rows / num_threads)

    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = []
        for i in range(num_threads):
            start = i * chunk_size
            end = (i + 1) * chunk_size
            chunk = df.iloc[start:end]
            future = executor.submit(chunk.apply(process_movie, axis=1))
            futures.append(future)

        # Wait for all threads to finish
        concurrent.futures.wait(futures)

        executor.shutdown()

    print(f"Error array: {error_array}")


def populate_genres(self, title: str) -> None:
    raise NotImplementedError
    database_movie_id = self.get_movie_by_title(title)[0]
    try:
        movie_id = tmdb.Search().movie(query=title)['results'][0]['id']
        movie = tmdb.Movies(movie_id)
        genres = movie.info()['genres']
        for genre in genres:
            try:
                # Search if genre exists in database
                self.cursor.execute("SELECT genre_id FROM Genre WHERE name LIKE ?", (genre['name'],))
                if self.cursor.fetchone() is None:
                    raise mariadb.DataError

            except mariadb.DataError as e:
                # Genre does not exist, insert into database
                print(f"Inserting into Genre: {genre['name']}")
                self.cursor.execute("INSERT INTO Genre (name) VALUES (?)", (genre['name'],))
                self.connection.commit()
            try:
                print(f"Inserting into Movie_Genre: {movie_id, self.get_genre_id(genre['name'])}")
                self.cursor.execute("INSERT INTO Movie_Genre (movie_id, genre_id) VALUES (?, ?)",
                                    (database_movie_id, self.get_genre_id(genre['name'])))
                self.connection.commit()
            except mariadb.DataError as e:
                pass
            except mariadb.IntegrityError as e:
                pass
    except IndexError as e:
        # Movie does not exist on TMDB
        pass


def get_actors_from_API(self, movie_id: int) -> list:
    raise NotImplementedError
    url = "https://api.themoviedb.org/3/movie/" + str(movie_id) + "/credits?language=en-US"
    print(url)

    headers = {"accept": "application/json",  # Header not working, insert your own API key, please see docs
               "Authorization": ""}

    response = requests.get(url, headers=headers)  # print(response.json()['crew'])  # return response.json()['crew']


def update_directors_for_db(self):
    raise NotImplementedError
    self.cursor.execute("SELECT * FROM Movie")
    for movie in self.cursor.fetchall():
        print(f"Updating movie: {movie[1]} with id: {movie[0]}")
        try:
            movie_id = tmdb.Search().movie(query=movie[1])['results'][0]['id']
        except IndexError as e:
            movie_id = None
            continue
        if movie_id is None or movie_id == 0:
            continue
        database_movie_id = movie[0]
        crew = self.get_actors_from_API(movie_id)
        for person in crew:
            try:
                if person['job'] == "Director" or person['job'] == "director":
                    name = person['name']
                    director_id = person['id']
                    try:
                        # Check if director exists in database
                        self.cursor.execute("SELECT director_id FROM Director WHERE director_name LIKE ?", (name,))
                        if self.cursor.fetchone() is None:
                            self.cursor.execute("INSERT INTO Director (director_name, tmdb_id) VALUES (?, ?)",
                                                (name, director_id))
                            self.connection.commit()
                        try:
                            # Get director_id from director table
                            self.cursor.execute("SELECT director_id FROM Director WHERE director_name LIKE ?", (name,))
                            director_db_id = self.cursor.fetchone()[0]
                            self.cursor.execute("INSERT INTO Movie_Director (movie_id, director_id) VALUES (?, ?)",
                                                (database_movie_id, director_db_id))
                            self.connection.commit()
                        except mariadb.IntegrityError as e:
                            pass
                    except mariadb.DataError as e:
                        # Director does not exist, insert into database
                        self.cursor.execute("INSERT INTO Director (director_name, tmdb_id) VALUES (?, ?)",
                                            (name, director_id))
                        self.connection.commit()
                        try:
                            self.cursor.execute("SELECT director_id FROM Director WHERE director_name LIKE ?", (name,))
                            director_db_id = self.cursor.fetchone()[0]
                            self.cursor.execute("INSERT INTO Movie_Director (movie_id, director_id) VALUES (?, ?)",
                                                (database_movie_id, director_db_id))
                            self.connection.commit()
                        except mariadb.IntegrityError as e:
                            pass
            except KeyError as e:
                pass


def update_actors_for_db(self):
    raise NotImplementedError
    self.cursor.execute("SELECT * FROM Movie")
    for movie in self.cursor.fetchall():
        try:
            movie_id = tmdb.Search().movie(query=movie[1])['results'][0]['id']
        except IndexError as e:
            movie_id = None
            continue
        if movie_id is None or movie_id == 0:
            continue
        database_movie_id = movie[0]
        actors = self.get_actors_from_API(movie_id)
        for actor in actors:
            name = actor['name']
            actor_id = actor['id']
            character = actor['character']
            try:
                # Check if actor exists in database
                self.cursor.execute("SELECT actor_id FROM Actor WHERE actor_name LIKE ?", (name,))
                if self.cursor.fetchone() is None:
                    self.cursor.execute("INSERT INTO Actor (actor_name, tmdb_id) VALUES (?, ?)", (name, actor_id))
                    self.connection.commit()
                else:
                    self.cursor.execute("UPDATE Actor SET tmdb_id = ? WHERE actor_name LIKE ?", (actor_id, name))
                    self.connection.commit()
            except mariadb.IntegrityError as e:
                with open("actors.txt", "a") as f:
                    f.write(f"[-] Error Inserting actor, {name} to Movie_Actor table\n {e}\n")
            except mariadb.DataError as e:
                with open("actors.txt", "a") as f:
                    f.write(f"[-] Error Inserting actor, {name} to Movie_Actor table\n {e}\n")
            try:
                # Actor ID is the actor_id in Actor table
                self.cursor.execute("SELECT actor_id FROM Actor WHERE actor_name LIKE ?", (name,))
                db_actor_id = self.cursor.fetchone()[0]
                if db_actor_id is not None:
                    # Check if actor is already in Movie_Actor table
                    self.cursor.execute("SELECT * FROM Movie_Actor WHERE movie_id = ? AND actor_id = ?",
                                        (database_movie_id, db_actor_id))
                    if self.cursor.fetchone() is None:
                        self.cursor.execute(
                            "INSERT INTO Movie_Actor (movie_id, actor_id, movie_character) VALUES (?, ?, ?)",
                            (database_movie_id, db_actor_id, character))
                        self.connection.commit()
                    else:
                        self.cursor.execute(
                            "UPDATE Movie_Actor SET movie_character = ? WHERE movie_id = ? AND actor_id = ?",
                            (character, database_movie_id, db_actor_id))
                        self.connection.commit()
            except mariadb.IntegrityError as e:
                f.write(f"[-] Error Inserting actor, {actor['name']} to Movie_Actor table\n {e}\n")
            except mariadb.DataError as e:
                with open("actors.txt", "a") as f:
                    f.write(f"[-] Error Inserting actor, {actor['name']} to Movie_Actor table\n {e}\n")


def parse_args() -> None:
    """
    Parse command line arguments
    -t, --table-create: Create tables in database (this uses the tables.sql file)
    -s, --seed: Seed database with data with SQL script
    :return: None
    """
    parser = argparse.ArgumentParser(
        description="**UNTESTED! RUN AT YOUR OWN RISK** Database Management System for Movie Database",
        prog="DBMS Movie")
    parser.add_argument("-m", "--migration", action="store_true", help="Run migration script (tables.sql)")
    parser.add_argument("-s", "--seed", action="store_true", help="Seed database with data (seed.sql)")
    args = parser.parse_args()

    config = configparser.ConfigParser()
    config.read('../../Config/config.ini')

    user = config.get('DBMS_MOVIE', 'USERNAME')
    password = config.get('DBMS_MOVIE', 'PASSWORD')
    host = config.get('DBMS_MOVIE', 'HOST')
    port = int(config.get('DBMS_MOVIE', 'PORT'))
    database = config.get('DBMS_MOVIE', 'DATABASE')
    try:
        connection = mariadb.connect(user=user, password=password, host=host, port=port, database=database)
        cursor = connection.cursor()
    except mariadb.Error as e:
        print(f"[-] Error connecting to database\n {e}")
        return

    def migration() -> None:
        """
        Create tables in database
        :return: None
        """
        with open("tables.sql", "r") as f:
            sql = f.read()
            try:
                cursor.execute(sql)
                connection.commit()
            except mariadb.DataError as e:
                print(f"[-] Error creating tables\n {e}")
                return
        print("[+] Tables created successfully")

    def seed_database() -> None:
        """
        Seed database with data
        :return: None
        """
        with open("seed.sql", "r") as f:
            sql = f.read()
            try:
                cursor.execute(sql)
                connection.commit()
            except mariadb.DataError as e:
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


if __name__ == "__main__":
    parse_args()
