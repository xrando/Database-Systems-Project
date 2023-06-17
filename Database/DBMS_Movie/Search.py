
# search
def search_directors(self, name: str) -> tuple:
    self.cursor.execute("SELECT * "
                        "FROM Director "
                        "WHERE director_name "
                        "LIKE %s LIMIT 30", ('%' + name + '%',))
    return self.cursor.fetchall()


def search_movies(self, name: str) -> tuple:
    self.cursor.execute("SELECT * "
                        "FROM Movie "
                        "WHERE title "
                        "LIKE %s"
                        "LIMIT 30", ('%' + name + '%',))
    return self.cursor.fetchall()


def search_actors(self, name: str) -> tuple:
    self.cursor.execute("SELECT * "
                        "FROM Actor "
                        "WHERE actor_name "
                        "LIKE %s"
                        "LIMIT 30", ('%' + name + '%',))
    return self.cursor.fetchall()
