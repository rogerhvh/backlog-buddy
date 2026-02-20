
import sqlite3
from pathlib import Path
from typing import Generator, Self

DATABASE_PATH = Path("data/games.db")
DATABASE_TEMP_PATH = Path("data/games_temp.db")
TABLE_NAME = "gameinfo"

class DatabaseNotOpened(Exception):
    def __init__(self):
        self.message = "Database connection does not exist. Please connect to or create a database."
        super().__init__(self.message)

class InvalidDatabaseName(Exception):
    def __init__(self):
        self.message = "Database can only have alphanumeric characters."
        super().__init__(self.message)

class GameDatabase():

    def __init__(self, temp=False):
        self._connection = None
        self._cursor = None
        if (temp):
            self._name = DATABASE_TEMP_PATH
        else:
            self._name = DATABASE_PATH 
    
    # I implemented a context manager to make database opening/
    # closing easier. 
    def __enter__(self) -> Self:
        self._connect_to_db()
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback) -> bool:
        self._close_connection()
        if exc_type is None:
            return True
        else:
            print(f"An error of type {exc_type} occured when accessing data in the database\n"\
                  f"Value given: {exc_value}\n"
                  f"Traceback: {exc_traceback}")
            return False

    def _connect_to_db(self) -> None:
        """
        Connects to the database and creates a cursor object.
        """
        self._connection = sqlite3.connect(self._name)
        self._cursor = self._connection.cursor()

    def create_database(self) -> None:
        """
        Creates database if one does not exist.
        """
        self._check_database_existence()
        self._cursor.execute(f"""CREATE TABLE IF NOT EXISTS {TABLE_NAME}
                    (
                        id INT PRIMARY KEY NOT NULL,
                        title TEXT NOT NULL,
                        genres TEXT NOT NULL,
                        idf REAL NOT NULL
                    );""")
        self._connection.commit()
    
    def drop_database(self, does_not_exist_ok: bool=False) -> None:
        """
        Drops database (if requested).
        """

        self._check_database_existence()
        if (not does_not_exist_ok):
            self._cursor.execute(f"""DROP TABLE {TABLE_NAME};""")
        else:
            self._cursor.execute(f"""DROP TABLE IF EXISTS {TABLE_NAME};""")\

        self._connection.commit()

    def _close_connection(self) -> None:
        """
        Closes the connection.
        """
        self._check_database_existence()

        self._cursor.close()
        self._connection.close()

    def insert(self, data: tuple[int | str]) -> None:
        """
        Inserts data into database. Assumes IDs are unique.
        """
        
        self._check_database_existence()
        self._cursor.execute(f"""
                INSERT INTO {TABLE_NAME} (id, title, genres, idf) VALUES (?, ?, ?, ?);
        """, (data[0], data[1], data[2], 0))
        self._connection.commit()

        print(f"- Inserted {data[1]} ({data[0]}) into database")
    
    def get_all_games_stored(self) -> set[int]:
        """
        Gets all games currently stored in the database.
        Can be slow since this is a linear operation.
        """

        self._check_database_existence()
        result = self._cursor.execute(f"""
            SELECT id FROM {TABLE_NAME};
        """)

        ret = set()
        for i in result.fetchall():
            ret.add(i[0])
        return ret
    
    def get_all_data(self) -> Generator[tuple, None, None]:
        """
        Gets all table data. Is a generator to save memory.
        """

        self._check_database_existence()
        result = self._cursor.execute(f"""
            SELECT * FROM {TABLE_NAME};
        """)

        for i in result.fetchall():
            yield i

    def get_genre(self, id: int) -> str:
        """
        Returns genre for each game ID.
        
        :param self: Description
        :param id: Game ID
        :type id: int
        :return: Genres separated by comma
        :rtype: str
        """

        if (id == -1):
            return "No genre information."

        self._check_database_existence()
        result = self._cursor.execute(f"""
            SELECT genres FROM {TABLE_NAME} WHERE id = ?;
        """, (id,))

        ret = result.fetchone()
        if (ret is not None):
            return ret[0]
        return "No genre information."
    
    def update_idf(self, id: int, idf: float) -> None:
        """
        Given a game ID, update the IDF for said game.
        """

        self._check_database_existence()
        self._cursor.execute(f"""
            UPDATE {TABLE_NAME} SET idf = ? WHERE id = ?;
                             """, (idf, id))
        self._connection.commit()
    
    def get_num_rows(self) -> int:

        self._check_database_existence()
        self._cursor.execute(f"SELECT COUNT(*) FROM {TABLE_NAME}")
        return self._cursor.fetchone()[0]

    def _check_database_existence(self) -> None:
        """
        Checks if database exists.
        
        :param self: Description
        """
        if (self._cursor is None):
            raise DatabaseNotOpened
