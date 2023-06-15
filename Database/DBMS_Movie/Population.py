def get_genre_id(self, genre_name: str) -> int:
    try:
        self.cursor.execute("SELECT genre_id FROM Genre WHERE name LIKE ?", (genre_name,))
        return self.cursor.fetchone()[0]
    except mariadb.DataError as e:
        # Genre does not exist
        pass


def get_release_date(self, movie: str) -> str:
    try:
        self.cursor.execute("SELECT release_date FROM Movie WHERE title LIKE ?", (movie,))
        return self.cursor.fetchone()[0].strftime("%B %d, %Y")
    except mariadb.DataError as e:
        # Movie does not exist
        pass


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


# Data Collection Functions (Do not use in production)

def populate_with_csv(self) -> None:
    raise NotImplementedError
    # Open the CSV file and read it into a pandas dataframe
    df = pd.read_csv(self.dataset)
    error_array = []

    # Insert first 3 columns into Movie table (id, title, synopsis), release data is the current date
    def process_movie(row):
        print(f"Inserting : {row['title'], row['overview']}")
        # Check if title is already in the database
        self.cursor.execute("SELECT title FROM Movie WHERE title = ?", (row["title"],))
        if self.cursor.fetchone() is not None:
            return
        release_date = self.get_release_date(row["title"]) or "2045-05-31"
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


def populate_genres(self, title: str) -> None:
    raise NotImplementedError
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


def get_actors_from_API(self, movie_id: int) -> list:
    raise NotImplementedError
    url = "https://api.themoviedb.org/3/movie/" + str(movie_id) + "/credits?language=en-US"
    print(url)

    headers = {"accept": "application/json",  # Header not working, insert your own API key, please see docs
               "Authorization": ""}

    response = requests.get(url, headers=headers)  # print(response.json()['crew'])  # return response.json()['crew']


def update_directors_for_db(self):
    raise NotImplementedError
    self.cursor.execute("SELECT * FROM Movie")
    for movie in self.cursor.fetchall():
        print(f"Updating movie: {movie[1]} with id: {movie[0]}")
        try:
            movie_id = tmdb.Search().movie(query=movie[1])['results'][0]['id']
        except IndexError as e:
            movie_id = None
            continue
        if movie_id is None or movie_id == 0:
            continue
        database_movie_id = movie[0]
        crew = self.get_actors_from_API(movie_id)
        for person in crew:
            try:
                if person['job'] == "Director" or person['job'] == "director":
                    name = person['name']
                    director_id = person['id']
                    try:
                        # Check if director exists in database
                        self.cursor.execute("SELECT director_id FROM Director WHERE director_name LIKE ?", (name,))
                        if self.cursor.fetchone() is None:
                            self.cursor.execute("INSERT INTO Director (director_name, tmdb_id) VALUES (?, ?)",
                                                (name, director_id))
                            self.connection.commit()
                        try:
                            # Get director_id from director table
                            self.cursor.execute("SELECT director_id FROM Director WHERE director_name LIKE ?", (name,))
                            director_db_id = self.cursor.fetchone()[0]
                            self.cursor.execute("INSERT INTO Movie_Director (movie_id, director_id) VALUES (?, ?)",
                                                (database_movie_id, director_db_id))
                            self.connection.commit()
                        except mariadb.IntegrityError as e:
                            pass
                    except mariadb.DataError as e:
                        # Director does not exist, insert into database
                        self.cursor.execute("INSERT INTO Director (director_name, tmdb_id) VALUES (?, ?)",
                                            (name, director_id))
                        self.connection.commit()
                        try:
                            self.cursor.execute("SELECT director_id FROM Director WHERE director_name LIKE ?", (name,))
                            director_db_id = self.cursor.fetchone()[0]
                            self.cursor.execute("INSERT INTO Movie_Director (movie_id, director_id) VALUES (?, ?)",
                                                (database_movie_id, director_db_id))
                            self.connection.commit()
                        except mariadb.IntegrityError as e:
                            pass
            except KeyError as e:
                pass


def update_actors_for_db(self):
    raise NotImplementedError
    self.cursor.execute("SELECT * FROM Movie")
    for movie in self.cursor.fetchall():
        try:
            movie_id = tmdb.Search().movie(query=movie[1])['results'][0]['id']
        except IndexError as e:
            movie_id = None
            continue
        if movie_id is None or movie_id == 0:
            continue
        database_movie_id = movie[0]
        actors = self.get_actors_from_API(movie_id)
        for actor in actors:
            name = actor['name']
            actor_id = actor['id']
            character = actor['character']
            try:
                # Check if actor exists in database
                self.cursor.execute("SELECT actor_id FROM Actor WHERE actor_name LIKE ?", (name,))
                if self.cursor.fetchone() is None:
                    self.cursor.execute("INSERT INTO Actor (actor_name, tmdb_id) VALUES (?, ?)", (name, actor_id))
                    self.connection.commit()
                else:
                    self.cursor.execute("UPDATE Actor SET tmdb_id = ? WHERE actor_name LIKE ?", (actor_id, name))
                    self.connection.commit()
            except mariadb.IntegrityError as e:
                with open("actors.txt", "a") as f:
                    f.write(f"[-] Error Inserting actor, {name} to Movie_Actor table\n {e}\n")
            except mariadb.DataError as e:
                with open("actors.txt", "a") as f:
                    f.write(f"[-] Error Inserting actor, {name} to Movie_Actor table\n {e}\n")
            try:
                # Actor ID is the actor_id in Actor table
                self.cursor.execute("SELECT actor_id FROM Actor WHERE actor_name LIKE ?", (name,))
                db_actor_id = self.cursor.fetchone()[0]
                if db_actor_id is not None:
                    # Check if actor is already in Movie_Actor table
                    self.cursor.execute("SELECT * FROM Movie_Actor WHERE movie_id = ? AND actor_id = ?",
                                        (database_movie_id, db_actor_id))
                    if self.cursor.fetchone() is None:
                        self.cursor.execute(
                            "INSERT INTO Movie_Actor (movie_id, actor_id, movie_character) VALUES (?, ?, ?)",
                            (database_movie_id, db_actor_id, character))
                        self.connection.commit()
                    else:
                        self.cursor.execute(
                            "UPDATE Movie_Actor SET movie_character = ? WHERE movie_id = ? AND actor_id = ?",
                            (character, database_movie_id, db_actor_id))
                        self.connection.commit()
            except mariadb.IntegrityError as e:
                f.write(f"[-] Error Inserting actor, {actor['name']} to Movie_Actor table\n {e}\n")
            except mariadb.DataError as e:
                with open("actors.txt", "a") as f:
                    f.write(f"[-] Error Inserting actor, {actor['name']} to Movie_Actor table\n {e}\n")


if __name__ == "__main__":
    raise NotImplementedError("Do not run this file")
