import sqlite3
from pathlib import Path
from typing import Self, Optional, List, Dict

DATABASE_PATH = Path("data/backlog_buddy.db")
PROFILES_TABLE = "user_profiles"

class DatabaseNotOpened(Exception):
    def __init__(self):
        self.message = "Database connection does not exist. Please connect to or create a database."
        super().__init__(self.message)

class UserProfileDatabase:
    def __init__(self):
        self._connection = None
        self._cursor = None
    
    def __enter__(self) -> Self:
        self._connect_to_db()
        return self
    
    def __exit__(self, exc_type, exc_value, exc_traceback) -> bool:
        self._close_connection()
        if exc_type is None:
            return True
        else:
            print(f"An error of type {exc_type} occurred when accessing data in the database\n"
                  f"Value given: {exc_value}\n"
                  f"Traceback: {exc_traceback}")
            return False
    
    def _connect_to_db(self) -> None:
        """Connects to the database and creates a cursor object."""
        self._connection = sqlite3.connect(self._name if hasattr(self, '_name') else DATABASE_PATH)
        self._cursor = self._connection.cursor()
    
    def _close_connection(self) -> None:
        """Closes the database connection."""
        if self._connection:
            self._connection.close()
    
    def _check_database_existence(self) -> None:
        """Checks if database file exists, creates it if not."""
        if not DATABASE_PATH.exists():
            DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    def create_database(self) -> None:
        """Creates the user profiles table if it does not exist."""
        self._check_database_existence()
        self._cursor.execute(f"""CREATE TABLE IF NOT EXISTS {PROFILES_TABLE}
                    (
                        user_id TEXT PRIMARY KEY NOT NULL,
                        steam_id TEXT NOT NULL UNIQUE,
                        preferred_genres TEXT,
                        min_playtime_hours INTEGER,
                        max_playtime_hours INTEGER,
                        creation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );""")
        self._connection.commit()
    
    def insert_profile(self, user_id: str, steam_id: str, preferred_genres: Optional[List[str]] = None,
                      min_playtime_hours: Optional[int] = None, max_playtime_hours: Optional[int] = None) -> None:
        """Inserts a new user profile."""
        if not self._connection:
            raise DatabaseNotOpened()
        
        genres_str = ','.join(preferred_genres) if preferred_genres else ''
        self._cursor.execute(f"""INSERT INTO {PROFILES_TABLE} 
                            (user_id, steam_id, preferred_genres, min_playtime_hours, max_playtime_hours)
                            VALUES (?, ?, ?, ?, ?)""",
                            (user_id, steam_id, genres_str, min_playtime_hours, max_playtime_hours))
        self._connection.commit()
    
    def get_profile_by_user_id(self, user_id: str) -> Optional[Dict]:
        """Fetches a profile by user_id."""
        if not self._connection:
            raise DatabaseNotOpened()
        
        self._cursor.execute(f"""SELECT * FROM {PROFILES_TABLE} WHERE user_id = ?""", (user_id,))
        row = self._cursor.fetchone()
        
        if row:
            return {
                'user_id': row[0],
                'steam_id': row[1],
                'preferred_genres': row[2].split(',') if row[2] else [],
                'min_playtime_hours': row[3],
                'max_playtime_hours': row[4],
                'creation_date': row[5],
                'last_updated': row[6]
            }
        return None
    
    def get_profile_by_steam_id(self, steam_id: str) -> Optional[Dict]:
        """Fetches a profile by steam_id."""
        if not self._connection:
            raise DatabaseNotOpened()
        
        self._cursor.execute(f"""SELECT * FROM {PROFILES_TABLE} WHERE steam_id = ?""", (steam_id,))
        row = self._cursor.fetchone()
        
        if row:
            return {
                'user_id': row[0],
                'steam_id': row[1],
                'preferred_genres': row[2].split(',') if row[2] else [],
                'min_playtime_hours': row[3],
                'max_playtime_hours': row[4],
                'creation_date': row[5],
                'last_updated': row[6]
            }
        return None
    
    def update_profile(self, user_id: str, steam_id: Optional[str] = None, 
                      preferred_genres: Optional[List[str]] = None,
                      min_playtime_hours: Optional[int] = None, 
                      max_playtime_hours: Optional[int] = None) -> None:
        """Updates a user profile."""
        if not self._connection:
            raise DatabaseNotOpened()
        
        updates = []
        params = []
        
        if steam_id:
            updates.append("steam_id = ?")
            params.append(steam_id)
        if preferred_genres is not None:
            updates.append("preferred_genres = ?")
            params.append(','.join(preferred_genres))
        if min_playtime_hours is not None:
            updates.append("min_playtime_hours = ?")
            params.append(min_playtime_hours)
        if max_playtime_hours is not None:
            updates.append("max_playtime_hours = ?")
            params.append(max_playtime_hours)
        
        updates.append("last_updated = CURRENT_TIMESTAMP")
        
        query = f"""UPDATE {PROFILES_TABLE} SET {', '.join(updates)} WHERE user_id = ?"""
        params.append(user_id)
        
        self._cursor.execute(query, params)
        self._connection.commit()
    
    def delete_profile(self, user_id: str) -> None:
        """Deletes a user profile."""
        if not self._connection:
            raise DatabaseNotOpened()
        
        self._cursor.execute(f"""DELETE FROM {PROFILES_TABLE} WHERE user_id = ?""", (user_id,))
        self._connection.commit()
    
    def profile_exists(self, user_id: str) -> bool:
        """Checks if a profile exists."""
        if not self._connection:
            raise DatabaseNotOpened()
        
        self._cursor.execute(f"""SELECT 1 FROM {PROFILES_TABLE} WHERE user_id = ? LIMIT 1""", (user_id,))
        return self._cursor.fetchone() is not None
