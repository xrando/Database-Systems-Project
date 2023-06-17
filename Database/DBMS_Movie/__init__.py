import mariadb
import sys
import tmdbsimple as tmdb
import configparser
import os

config = configparser.ConfigParser()
config_route = os.path.join(os.path.dirname(__file__), '..', '..', 'Config', 'config.ini')

try:
    config.read(config_route)
except configparser.Error as e:
    print(f"Error reading config file: {e}")


class DBMS_Movie:
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

                # Migration untested here
                # TODO: Test migration
                from Migration import create_tables, seed
                create_tables(self.cursor)
                seed(self.cursor)
            except mariadb.Error as e:
                print(f"Error connecting to MariaDB Platform: {e}")
                sys.exit(1)
        except mariadb.OperationalError as e:
            print(f"Error connecting to MariaDB Platform: {e}")
            sys.exit(1)

    from .Movie import Movie_list, get_movie_by_title,get_pages, carousel
    from .Actor import Actor
    from .Director import Director
    from .Search import search_movies, search_directors, search_actors, get_movieID

