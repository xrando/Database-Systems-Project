# The Movie Database

## Installation

Packages required:
- Python 3
- pip
- MySQL (MariaDB)
- MongoDB Community Server

```bash
$ pip install -r requirements.txt
```

>Note: Do ensure that mysql & mariadb is running before running the program. mysql should be in $PATH

If you are unable to seed the database, you can run the following command to create the database and tables.
```bash
$ mysql --database=DBMS_Movie -u root -p password -h localhost -P 3306 < Seed.sql
```
The migration and seed file for the movie database is included at `Database/DBMS_Movie/Seed.sql`

## Configuration
Configuration files are stored in `Config/config.ini` folder. You can change the configuration by editing the files.

```bash
cp Sample.Config.ini config.ini
```

### TMDB Access Token
```
[TMDB]
API_KEY =
ACCESS_TOKEN =
```

To get the API_KEY and ACCESS_TOKEN, you need to register an account on [TMDB](https://www.themoviedb.org/). After that, you can get the API_KEY and ACCESS_TOKEN from [here](https://www.themoviedb.org/settings/api).

### MySQL
```
[DBMS_MOVIE]
HOST = 127.0.0.1
PORT = 3306 # Change to your MySQL port
USERNAME = root # Change to your MySQL username
PASSWORD = root # Change to your MySQL password
DATABASE = DBMS_Movie

[DBMS_USER]
HOST = 127.0.0.1
PORT = 3306 # Change to your MySQL port
USERNAME = root # Change to your MySQL username
PASSWORD = root # Change to your MySQL password
DATABASE = DBMS_User
```

### Flask
```
[FLASK]
HOST = 0.0.0.0
PORT = 5000
DEBUG = True
LOG_FILE = log/file/path # Change to your log file path
```

# Running the program
```bash
$ python app.py
```

OR
```bash
$ flask run
```

## Troubleshooting

The movie database will be automatically seeded with the data from the seedfile, but if you encounter any error, you can run the following command to seed the database.

```bash
$ mysql --database=DBMS_Movie -u root -p password -h localhost -P 3306 < Seed.sql
```
The migration and seed file for the movie database is included at `Database/DBMS_Movie/Seed.sql`

Internet connection will be required to access the TMDB API.

### Application crash after multiple request for movie details
This is a known issue (TMDB rate limit). You can try to run the program again.

The program will be stable after caching the data.