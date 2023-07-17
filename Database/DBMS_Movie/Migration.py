####################################################################################################
# These are the functions for Database Migration, which is used to seed the database with data.    #
# DBMS_Movie is automatically seeded upon running the application.(app.py)                         #
####################################################################################################

from Config.ConfigManager import ConfigManager
import argparse
import os
import subprocess

config_manager = ConfigManager()
# Get the configuration
config = config_manager.get_config()

database, user, password, host, port = (
    config.get('DBMS_MOVIE', 'DATABASE'),
    config.get('DBMS_MOVIE', 'USERNAME'),
    config.get('DBMS_MOVIE', 'PASSWORD'),
    config.get('DBMS_MOVIE', 'HOST'),
    config.get('DBMS_MOVIE', 'PORT')
)


def seed(seed_file: str = None) -> None:
    """
    Seeds the database with the data from the seed_file. MySQL must be installed and in the PATH

    :param seed_file: The file to seed the database with
    :type seed_file: str
    :return: None
    """

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
        exit(1)

    try:
        command = f"mysql --database {database} -u {user} -p{password} -h {host} -P {port} < '{seed_file}'"
        subprocess.run(command, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"[-] Error seeding database\n {e}")
        exit(1)

    print("[+] Database seeded successfully")


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


def parse_args() -> None:
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
        prog="python3 Migration.py"
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

    action_map = {"migration": migration, "seed": seed}

    for action, func in action_map.items():
        if getattr(args, action):
            func()
            return
    else:
        parser.print_help()


if __name__ == "__main__":
    parse_args()
