import mariadb
import sys
import pandas as pd
import tmdbsimple as tmdb
import configparser
import concurrent.futures
import math
from pprint import pprint


class Database:
    dataset = "TMDB_updated.csv"

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
            print("Please enter your TMDB API key in the config.ini file")
            sys.exit(1)

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

        :param: None
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
                       "wiki_link VARCHAR(255) NOT NULL);"
        create_director = "CREATE TABLE IF NOT EXISTS Director (" \
                          "director_id INT AUTO_INCREMENT PRIMARY KEY, " \
                          "director_name VARCHAR(255) NOT NULL, " \
                          "wiki_link VARCHAR(255) NOT NULL);"
        create_movie_actor = "CREATE TABLE IF NOT EXISTS Movie_Actor (" \
                             "movie_id INT NOT NULL, " \
                             "actor_id INT NOT NULL, " \
                             "PRIMARY KEY (movie_id, actor_id), " \
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

    def seed(self) -> None:
        # Open the CSV file and read it into a pandas dataframe
        df = pd.read_csv(self.dataset)
        error_array = []

        # Insert first 3 columns into Movie table (id, title, synopsis), release data is the current date
        def process_movie(row):
            print(f"Inserting : {row['title'], row['overview']}")
            release_date = self.get_release_date(row["title"]) or "2025-05-01"
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

    def get_movie(self, movie_id: int) -> tuple:
        self.cursor.execute("SELECT * FROM Movie WHERE movie_id = ?", (movie_id,))
        return self.cursor.fetchone()

    def get_movie_by_title(self, title: str) -> tuple:
        self.cursor.execute("SELECT * FROM Movie WHERE title = ?", (title,))
        return self.cursor.fetchone()

    def populate_genres(self, title: str) -> None:
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

    def get_genre_id(self, genre_name: str) -> int:
        try:
            self.cursor.execute("SELECT genre_id FROM Genre WHERE name LIKE ?", (genre_name,))
            return self.cursor.fetchone()[0]
        except mariadb.DataError as e:
            # Genre does not exist
            pass

    def get_release_date(self, movie: str) -> str:
        try:
            release_date = tmdb.Search().movie(query=movie)['results'][0]['release_date']
            return release_date
        except IndexError as e:
            return "2025-05-01"

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


if __name__ == "__main__":
    db = Database()
    # db.create_tables()
    # db.seed()

    # Movie = tmdb.Search().movie(query="The Matrix")['results'][0]
    # stuff = tmdb.Movies(Movie).info()

    # pprint(Movie)
