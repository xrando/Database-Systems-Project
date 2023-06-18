from Config.ConfigManager import ConfigManager

config_manager = ConfigManager()

# Get the configuration
config = config_manager.get_config()

database = config.get('DBMS_MOVIE', 'DATABASE')
user = config.get('DBMS_MOVIE', 'USERNAME')
password = config.get('DBMS_MOVIE', 'PASSWORD')


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
