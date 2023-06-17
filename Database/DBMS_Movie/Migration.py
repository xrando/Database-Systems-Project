import mariadb
import sys


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
