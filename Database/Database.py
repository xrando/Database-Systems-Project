import mariadb
import sys
import pandas as pd
import tmdbsimple as tmdb
import configparser
import concurrent.futures
import math
import requests


class Database:

    def __init__(self) -> None:
        """
        Database Constructor, connects to the database and creates the tables if they do not exist

        All Configurations are stored in the config.ini file in path ../Config/config.ini
        """
        config = configparser.ConfigParser()
        config.read('../Config/config.ini')

        user = config.get('MARIADB_SERVER', 'USERNAME')
        password = config.get('MARIADB_SERVER', 'PASSWORD')
        host = config.get('MARIADB_SERVER', 'HOST')
        port = int(config.get('MARIADB_SERVER', 'PORT'))
        database = config.get('MARIADB_SERVER', 'DATABASE')
        tmdb.API_KEY = config.get('TMDB', 'API_KEY')

        if tmdb.API_KEY == "":
            raise ValueError("Please enter your TMDB API key in the config.ini file")

        try:
            self.connection = mariadb.connect(user=user,
                                              password=password,
                                              host=host,
                                              port=port,
                                              database=database)

            self.cursor = self.connection.cursor()
        except mariadb.DatabaseError as e:
            # Try to create database
            try:
                self.connection = mariadb.connect(user=user,
                                                  password=password,
                                                  host=host,
                                                  port=port)
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

        create_movie = "CREATE TABLE IF NOT EXISTS Movie (" \
                       "movie_id INT AUTO_INCREMENT PRIMARY KEY, " \
                       "title VARCHAR(255) NOT NULL, " \
                       "release_date DATE NOT NULL, " \
                       "synopsis TEXT NOT NULL);"

        create_genre = "CREATE TABLE IF NOT EXISTS Genre (" \
                       "genre_id INT AUTO_INCREMENT PRIMARY KEY, " \
                       "name VARCHAR(255) NOT NULL UNIQUE);"

        create_movie_genre = "CREATE TABLE IF NOT EXISTS Movie_Genre (" \
                             "movie_id INT NOT NULL, " \
                             "genre_id INT NOT NULL, " \
                             "PRIMARY KEY (movie_id, genre_id), " \
                             "FOREIGN KEY (movie_id) REFERENCES Movie(movie_id), " \
                             "FOREIGN KEY (genre_id) REFERENCES Genre(genre_id));"
        create_actor = "CREATE TABLE IF NOT EXISTS Actor (" \
                       "actor_id INT AUTO_INCREMENT PRIMARY KEY, " \
                       "actor_name VARCHAR(255) NOT NULL, " \
                       "tmdb_id VARCHAR(255) NOT NULL);"
        create_director = "CREATE TABLE IF NOT EXISTS Director (" \
                          "director_id INT AUTO_INCREMENT PRIMARY KEY, " \
                          "director_name VARCHAR(255) NOT NULL, " \
                          "tmdb_id VARCHAR(255) NOT NULL);"
        # "PRIMARY KEY (movie_id, actor_id, movie_character), " \
        create_movie_actor = "CREATE TABLE IF NOT EXISTS Movie_Actor (" \
                             "movie_id INT NOT NULL, " \
                             "actor_id INT NOT NULL, " \
                             "movie_character TEXT NOT NULL," \
                             "FOREIGN KEY (movie_id) REFERENCES Movie(movie_id), " \
                             "FOREIGN KEY (actor_id) REFERENCES Actor(actor_id));"
        create_movie_director = "CREATE TABLE IF NOT EXISTS Movie_Director (" \
                                "movie_id INT NOT NULL, " \
                                "director_id INT NOT NULL, " \
                                "PRIMARY KEY (movie_id, director_id), " \
                                "FOREIGN KEY (movie_id) REFERENCES Movie(movie_id), " \
                                "FOREIGN KEY (director_id) REFERENCES Director(director_id));"

        # Create the tables in the database
        self.cursor.execute(create_movie)
        self.cursor.execute(create_genre)
        self.cursor.execute(create_movie_genre)
        self.cursor.execute(create_actor)
        self.cursor.execute(create_director)
        self.cursor.execute(create_movie_actor)
        self.cursor.execute(create_movie_director)

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

    def get_movie_by_title(self, title: str) -> tuple:
        self.cursor.execute("SELECT * FROM Movie WHERE title = ?", (title,))
        return self.cursor.fetchone()

    def Actor(self,
              actor_name: str = None,
              actor_tmdb_id: str = None,
              order_by = None
              ) -> list[tuple]:
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
        orders = {
            "release_date": "release_date",
            "title": "title",
            "movie_id": "movie_id"
        }
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

    def Director(self,
                 director_name: str = None,
                 director_tmdb_id: str = None,
                 order_by=None
                 ) -> list[tuple]:
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
        orders = {
            "release_date": "release_date",
            "title": "title"
        }
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
        Returns a list of 5 movies that are closest to release date
        :return: List of movies (title, release_date, banner)
        :rtype: list[tuple]
        """
        poster_link = "https://image.tmdb.org/t/p/original"
        result = []

        stmt = "SELECT title, release_date " \
               "FROM Movie " \
               "WHERE release_date > CURRENT_DATE() " \
               "ORDER BY release_date ASC " \
               "LIMIT 5;"
        self.cursor.execute(stmt)
        movies = self.cursor.fetchall()
        for movie in movies:
            # Use tmdb api to get the image link
            try:
                movie_id = tmdb.Search().movie(query=movie[0])['results'][0]['id']
                movie_info = tmdb.Movies(movie_id).info()

                if movie_info is not None:
                    if movie_info['backdrop_path'] is not None:
                        banner = poster_link + movie_info['backdrop_path']
                    else:
                        banner = None
                else:
                    banner = None
            except IndexError:
                # Not all movies we have in the database are in the tmdb database
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

        headers = {
            "accept": "application/json",
            # Header not working, insert your own API key, please see docs
            "Authorization": ""
        }

        response = requests.get(url, headers=headers)
        # print(response.json()['crew'])
        # return response.json()['crew']

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
                                self.cursor.execute("SELECT director_id FROM Director WHERE director_name LIKE ?",
                                                    (name,))
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
                                self.cursor.execute("SELECT director_id FROM Director WHERE director_name LIKE ?",
                                                    (name,))
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
                        self.cursor.execute("INSERT INTO Actor (actor_name, tmdb_id) VALUES (?, ?)",
                                            (name, actor_id))
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


if __name__ == "__main__":
    db = Database()

    # Printing all movies in pages
    print(f"Page 1 of {db.get_pages_left(pages=1, limit=10)}")
    print(db.Movie_list(page=1, limit=10))

    print(f"Page 2 of {db.get_pages_left(pages=2, limit=10)}")
    print(db.Movie_list(page=2, limit=10))

    # Actors with name
    print(db.Actor(actor_name="Tom Hanks", order_by=["movie_id", "DESC"]))

    # Actors with tmdb_id
    print(db.Actor(actor_tmdb_id="31"))

    # Directors with name
    print(db.Director(director_name="Steven Spielberg"))
    
    # Directors with tmdb_id
    print(db.Director(director_tmdb_id="488"))

    # Carousels
    print(db.carousel())
