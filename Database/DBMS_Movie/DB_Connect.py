import configparser
import sys
import tmdbsimple as tmdb
import mariadb


class DBConnection:
    _instance = None

    def __new__(cls):
        if not cls._instance:
            cls._instance = super().__new__(cls)
            cls._instance.connection = cls._instance._create_connection()
            cls._instance.cursor = cls._instance.connection.cursor()
        return cls._instance

    def _create_connection(self):
        from Config.ConfigManager import ConfigManager

        config_manager = ConfigManager()
        config = config_manager.get_config()

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
        try:
            connection = mariadb.connect(
                user=config.get('DBMS_MOVIE', 'USERNAME'),
                password=config.get('DBMS_MOVIE', 'PASSWORD'),
                host=config.get('DBMS_MOVIE', 'HOST'),
                port=int(config.get('DBMS_MOVIE', 'PORT')),
                database=config.get('DBMS_MOVIE', 'DATABASE')
            )
            return connection
        except mariadb.ProgrammingError as e:
            print(f"You don't have a database named {database} in your MariaDB instance, creating it now...")
            try:
                connection = mariadb.connect(
                    user=user,
                    password=password,
                    host=host,
                    port=port
                )
                cursor = connection.cursor()
                cursor.execute("CREATE DATABASE IF NOT EXISTS " + database)
                cursor.execute("USE " + database)

                from .Migration import seed
                seed()

                return connection
            except mariadb.Error as e:
                print(f"Error connecting to MariaDB Platform: {e}")
                sys.exit(1)
        except mariadb.OperationalError as e:
            print(f"Error connecting to MariaDB Platform: {e}")
            sys.exit(1)

    def close_connection(self):
        self.cursor.close()
        self.connection.close()
