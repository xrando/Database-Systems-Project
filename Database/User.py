import mariadb
from Database.DB_User_Connect import UserDBConnection

# DBMS_Movie DB Connection
connection = UserDBConnection().connection
cursor = connection.cursor()

class Database:
    # User functions
    def get_user_by_id(self, id: int) -> tuple:
        try:
            cursor.execute("SELECT * FROM User WHERE id = ?", (id,))
        except mariadb.DataError as e:
            print(f"[-] Error retrieving user from database\n {e}")
        return cursor.fetchone()

    def get_password_by_username(self, username: str) -> tuple:
        try:
            cursor.execute("SELECT id, password FROM User WHERE username = ?", (username,))
        except mariadb.DataError as e:
            print(f"[-] Error retrieving user from database\n {e}")
        return cursor.fetchone()

    def check_username_exists(self, username: str) -> bool:
        try:
            cursor.execute("SELECT id FROM User WHERE username = ?", (username,))
        except mariadb.DataError as e:
            print(f"[-] Error retrieving user from database\n {e}")
        return cursor.fetchone() is not None

    def create_user(self, username: str, password: str, profilename: str, email: str, dob: str) -> None:
        try:
            cursor.execute("INSERT INTO User (username, password, profilename, email, dob) VALUES (?, ?, ?, ?, ?)",
                                (username, password, profilename, email, dob))
        except mariadb.DataError as e:
            print(f"[-] Error creating user in database\n {e}")
        connection.commit()

    def update_user(self, id: int, username: str, password: str, profilename: str, email: str, dob: str) -> None:
        try:
            cursor.execute(
                "UPDATE User SET username = ?, password = ?, profilename = ?, email = ?, dob = ? WHERE id = ?",
                (username, password, profilename, email, dob, id))
        except mariadb.DataError as e:
            print(f"[-] Error updating user in database\n {e}")
        connection.commit()

    def search_user(self, name: str) -> tuple:
        try:
            cursor.execute("SELECT * "
                                "FROM User "
                                "WHERE profilename "
                                "LIKE ?"
                                "AND username != 'admin' "
                                "LIMIT 30", ('%' + name + '%',))
        except mariadb.DataError as e:
            print(f"[-] Error searching for users from database\n {e}")
        return cursor.fetchall()

    def delete_user(self, id: int) -> None:
        try:
            cursor.execute("DELETE FROM User WHERE id = ?", (id,))
        except mariadb.DataError as e:
            print(f"[-] Error deleting user from database\n {e}")
        # connection.commit()

    def manual_commit(self) -> None:
        connection.commit()

    def manual_rollback(self) -> None:
        connection.rollback()
