#search
def search_directors(self, name: str) -> tuple:
    self.cursor.execute("SELECT * "
                        "FROM director "
                        "WHERE director_name "
                        "LIKE %s"
                        "LIMIT 30", ('%' + name + '%',))
    return self.cursor.fetchall()
def search_movies(self, name: str) -> tuple:
    self.cursor.execute("SELECT * "
                        "FROM movie "
                        "WHERE title "
                        "LIKE %s"
                        "LIMIT 30", ('%' + name + '%',))
    return self.cursor.fetchall()
def search_actors(self, name: str) -> tuple:
    self.cursor.execute("SELECT * "
                        "FROM actor "
                        "WHERE actor_name "
                        "LIKE %s"
                        "LIMIT 30", ('%' + name + '%',))
    return self.cursor.fetchall()

def get_movieID(self, title: str) -> int:
    self.cursor.execute("SELECT movie_id "
                        "FROM movie "
                        "WHERE title = %s", (title,))
    return self.cursor.fetchone()[0]