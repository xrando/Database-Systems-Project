import mariadb
import sys
from .DB_Connect import DBConnection
from .ConfigManager import ConfigManager

config_manager = ConfigManager()

# Get the configuration
config = config_manager.get_config()

database = config.get('DBMS_MOVIE', 'DATABASE')
user = config.get('DBMS_MOVIE', 'USERNAME')
password = config.get('DBMS_MOVIE', 'PASSWORD')


def create_tables() -> None:
    raise NotImplementedError("Use seed() instead")
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
        cursor.execute("USE DBMS_Movie")
    except mariadb.Error as e:
        print(f"Error connecting to MariaDB Platform: {e}")
        sys.exit(1)

    # Open the table file
    with open(movie_table_file, 'r') as f:
        # Execute the table file
        try:
            cursor.execute(f.read())
        except mariadb.Error as e:
            print(f"Error executing table file: {e}")
            sys.exit(1)


def seed(seed_file: str = None) -> None:
    """
    Seeds the database with the data from the seed_file. MySQL must be installed and in the PATH

    :param seed_file: The file to seed the database with
    :type seed_file: str
    :return: None
    """
    import os
    import subprocess

    if seed_file is None:
        seed_file = "Seed.sql"
        seed_file = os.path.join(os.path.dirname(__file__), seed_file)
        print(f"[+] No seed file specified, using default seed file: {seed_file}")

    if not os.path.exists(seed_file):
        print(f"[-] Error: {seed_file} does not exist")
        return

    # Check if mysql is installed
    try:
        subprocess.run("mysql --version", shell=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"[-] Error: mysql is not installed\n {e}")
        return

    try:
        command = f"mysql --database {database} -u {user} -p{password} < '{seed_file}'"
        subprocess.run(command, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"[-] Error seeding database\n {e}")
        return

    print("[+] Database seeded successfully")