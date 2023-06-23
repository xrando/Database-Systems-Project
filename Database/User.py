import mariadb
import sys
from Config.ConfigManager import ConfigManager


class Database:

    def __init__(self) -> None:
        """
        Database Constructor, connects to the database and creates the tables if they do not exist

        All Configurations are stored in the config.ini file in path ../Config/config.ini
        """
        # Initialize the config manager
        config_manager = ConfigManager()

        # Get the configuration
        config = config_manager.get_config()

        user = config.get('DBMS_USER', 'USERNAME')
        password = config.get('DBMS_USER', 'PASSWORD')
        host = config.get('DBMS_USER', 'HOST')
        port = int(config.get('DBMS_USER', 'PORT'))
        database = config.get('DBMS_USER', 'DATABASE')

        try:
            self.connection = mariadb.connect(user=user,
                                              password=password,
                                              host=host,
                                              port=port,
                                              database=database)

            self.cursor = self.connection.cursor()
            print("[+] Connected to Database")
        except mariadb.ProgrammingError as e:
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
                self.seed("DBMS_User.sql")
            except mariadb.Error as e:
                print(f"Error connecting to MariaDB Platform: {e}")
                sys.exit(1)

    def create_tables(self) -> None:
        create_user = "CREATE TABLE IF NOT EXISTS User (" \
                      "id INT auto_increment NOT NULL, " \
                      "username VARCHAR(255) NOT NULL, " \
                      "password VARCHAR(255) NOT NULL, " \
                      "profilename VARCHAR(255) NOT NULL, " \
                      "email VARCHAR(255) NOT NULL, " \
                      "dob DATE NOT NULL, " \
                      "PRIMARY KEY (id, username));"

        # Create the tables in the database
        self.cursor.execute(create_user)

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
            self.cursor.execute("USE DBMS_User")
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

    # User functions
    def get_user_by_id(self, id: int) -> tuple:
        try:
            self.cursor.execute("SELECT * FROM User WHERE id = ?", (id,))
        except mariadb.DataError as e:
            print(f"[-] Error retrieving user from database\n {e}")
        return self.cursor.fetchone()


    def get_password_by_username(self, username: str) -> tuple:
        try:
            self.cursor.execute("SELECT id, password FROM User WHERE username = ?", (username,))
        except mariadb.DataError as e:
            print(f"[-] Error retrieving user from database\n {e}")
        return self.cursor.fetchone()

    def check_username_exists(self, username: str) -> bool:
        try:
            self.cursor.execute("SELECT id FROM User WHERE username = ?", (username,))
        except mariadb.DataError as e:
            print(f"[-] Error retrieving user from database\n {e}")
        return self.cursor.fetchone() is not None

    def create_user(self, username: str, password: str, profilename: str, email: str, dob: str) -> None:
        try:
            self.cursor.execute("INSERT INTO User (username, password, profilename, email, dob) VALUES (?, ?, ?, ?, ?)",
                                (username, password, profilename, email, dob))
        except mariadb.DataError as e:
            print(f"[-] Error creating user in database\n {e}")
        self.connection.commit()

    def update_user(self, id: int, username: str, password: str, profilename: str, email: str, dob: str) -> None:
        try:
            self.cursor.execute(
                "UPDATE User SET username = ?, password = ?, profilename = ?, email = ?, dob = ? WHERE id = ?",
                (username, password, profilename, email, dob, id))
        except mariadb.DataError as e:
            print(f"[-] Error updating user in database\n {e}")
        self.connection.commit()
        
    def search_user(self, name: str) -> tuple:
        try:
            self.cursor.execute("SELECT * "
                           "FROM User "
                           "WHERE profilename "
                           "LIKE ?"
                           "LIMIT 30", ('%' + name + '%',))
        except mariadb.DataError as e:
            print(f"[-] Error searching for users from database\n {e}")
        return self.cursor.fetchall()

if __name__ == "__main__":
    db = Database()

    # Retrieving user
    user = db.get_password_by_username("admin")
    print(user)
    user = db.get_user_by_id(2200559)
    print(user)
