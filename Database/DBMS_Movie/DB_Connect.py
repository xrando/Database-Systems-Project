####################################################################################################
# This class is to create and maintain a connection to the database. It is a singleton class,      #
# meaning that only one instance of this class can exist at a time. This is to prevent multiple    #
# connections to the database being created.                                                       #
####################################################################################################
import configparser
import logging
import sys

import mariadb
import tmdbsimple as tmdb


class DBConnection:
    """
    Singleton class to create a connection to the database
    """
    _instance = None

    def __new__(cls) -> object:
        """
        Create a new instance of the class if it doesn't exist, otherwise return the existing instance
        """
        if not cls._instance:
            cls._instance = super().__new__(cls)
            cls._instance.connection = cls._instance._create_connection()
            cls._instance.cursor = cls._instance.connection.cursor()
        return cls._instance

    def _create_connection(self) -> mariadb.Connection:
        """
        Create a connection to the database

        :return: A connection to the database
        :rtype: mariadb.Connection
        """
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
            logging.error(f"Error reading config file: {e}")
            sys.exit(1)

        try:
            connection = mariadb.connect(
                user=user,
                password=password,
                host=host,
                port=port,
                database=database
            )
            return connection
        except mariadb.ProgrammingError as e:
            logging.info(f"Error connecting to MariaDB Platform: {e}, attempting to create database")
            print(f"You don't have a database named {database} in your MariaDB instance, creating it now...")
            try:
                connection = mariadb.connect(
                    user=user,
                    password=password,
                    host=host,
                    port=port
                )
                cursor = connection.cursor()
                cursor.execute(f"CREATE DATABASE IF NOT EXISTS {database}")
                cursor.execute(f"USE {database}")

                from .Migration import seed
                seed()

                logging.info(f"Successfully created database {database} and seeded it with data")
                return connection
            except mariadb.Error as e:
                logging.error(f"Error creating database: {e}")
                sys.exit(1)
        except mariadb.OperationalError as e:
            logging.error(f"Error connecting to MariaDB Platform: {e}")
            sys.exit(1)

    def close_connection(self) -> None:
        """
        Close the connection to the database
        :return: None
        """
        self.cursor.close()
        self.connection.close()
