# backend/services/profile_service.py
from database.database import UserProfileDatabase
from models import UserProfile
from typing import Optional, List

class ProfileService:
    def __init__(self):
        pass
    
    def create_profile(self, user_id: str, steam_id: str, preferred_genres: Optional[List[str]] = None,
                      min_playtime_hours: Optional[int] = None, max_playtime_hours: Optional[int] = None) -> UserProfile:
        """Creates a new user profile."""
        with UserProfileDatabase() as db:
            db.create_database()
            
            # Check if profile already exists
            if db.profile_exists(user_id):
                raise ValueError(f"Profile with user_id {user_id} already exists")
            
            db.insert_profile(user_id, steam_id, preferred_genres, min_playtime_hours, max_playtime_hours)
            
            # Retrieve and return the created profile
            profile_dict = db.get_profile_by_user_id(user_id)
            return UserProfile(**profile_dict)
    
    def get_profile_by_user_id(self, user_id: str) -> Optional[UserProfile]:
        """Retrieves a profile by user_id."""
        with UserProfileDatabase() as db:
            db.create_database()
            profile_dict = db.get_profile_by_user_id(user_id)
            
            if profile_dict:
                return UserProfile(**profile_dict)
            return None
    
    def get_profile_by_steam_id(self, steam_id: str) -> Optional[UserProfile]:
        """Retrieves a profile by steam_id."""
        with UserProfileDatabase() as db:
            db.create_database()
            profile_dict = db.get_profile_by_steam_id(steam_id)
            
            if profile_dict:
                return UserProfile(**profile_dict)
            return None
    
    def update_profile(self, user_id: str, steam_id: Optional[str] = None,
                      preferred_genres: Optional[List[str]] = None,
                      min_playtime_hours: Optional[int] = None,
                      max_playtime_hours: Optional[int] = None) -> UserProfile:
        """Updates a user profile."""
        with UserProfileDatabase() as db:
            db.create_database()
            
            # Check if profile exists
            if not db.profile_exists(user_id):
                raise ValueError(f"Profile with user_id {user_id} does not exist")
            
            db.update_profile(user_id, steam_id, preferred_genres, min_playtime_hours, max_playtime_hours)
            
            # Retrieve and return the updated profile
            profile_dict = db.get_profile_by_user_id(user_id)
            return UserProfile(**profile_dict)
    
    def delete_profile(self, user_id: str) -> bool:
        """Deletes a user profile."""
        with UserProfileDatabase() as db:
            db.create_database()
            
            # Check if profile exists
            if not db.profile_exists(user_id):
                raise ValueError(f"Profile with user_id {user_id} does not exist")
            
            db.delete_profile(user_id)
            return True
    
    def profile_exists(self, user_id: str) -> bool:
        """Checks if a profile exists."""
        with UserProfileDatabase() as db:
            db.create_database()
            return db.profile_exists(user_id)
