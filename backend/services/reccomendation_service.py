# backend/services/recommendation_service.py

import sqlite3
from data.game_database import GameDatabse
import requests
import time
from threading import Event

class RecommendationService:

    def __init__(self):
        self._game_database: GameDatabse = GameDatabse()
        with self._game_database as database:
            database.create_database()
            self._games_stored: set[int] = database.get_all_games_stored()
        
        self.getting_genres_mutex = Event()        # Mutex for background thread running
        self.writing_to_database_mutex = Event()   # Mutex for database modification
        self.checking_games_stored_mutex = Event() # Mutex for checking/modifying self._games_stored
        self.getting_genres_mutex.set()
        self.writing_to_database_mutex.set()
        self.checking_games_stored_mutex.set()

    def rank_games(self, games, time_available=120):
        """        
        args:
            games: List of game dictionaries from Steam API
            time_available: user's available time in minutes
        """
        scored_games = []
        
        for game in games:
            score = self._calculate_score(game, time_available)

            self.writing_to_database_mutex.wait()
            self.writing_to_database_mutex.clear()
            with self._game_database as database:
                genre = database.get_genre(game["appid"])
            self.writing_to_database_mutex.set()

            scored_games.append({
                **game,
                'recommendation_score': score,
                'genres': genre
            })
        
        # sorted in descendingo rder
        scored_games.sort(key=lambda x: x['recommendation_score'], reverse=True)
        return scored_games
    
    # tentative scoring function, can refine later
    def _calculate_score(self, game, time_available):
        score = 0
        
        # factor 1: recent playtime (higher = more engaged)
        playtime_2weeks = game.get('playtime_2weeks', 0)
        score += playtime_2weeks * 0.5
        
        # factor 2: total playtime (shows investment)
        playtime_forever = game.get('playtime_forever', 0)
        score += min(playtime_forever / 60, 100) * 0.3  # Cap at 100 hours
        
        # factor 3: has started but not finished (engagement signal)
        if 0 < playtime_forever < 300:  # Less than 5 hours
            score += 20
        
        # factor 4: time availability match (placeholder)
        # TODO: integrate with IGDB for actual completion times
        if time_available < 60:  # short session
            if playtime_forever > 0:  # prefer games already started
                score += 15
        
        return score
    
    def check_if_games_stored(self, game_data: dict) -> bool:
        """
        Checks if user games are in the database. If one game
        is missing, return False. Else, true.
        
        :param self: Description
        :param game_data: User game data from API
        :type game_data: dict
        :return: Whether database has all games or not
        :rtype: bool
        """
        
        games = game_data.get("games", [])

        self.checking_games_stored_mutex.wait()
        self.checking_games_stored_mutex.clear()

        for game in games:
            if (game["appid"] not in self._games_stored):
                self.checking_games_stored_mutex.set()
                return False
        self.checking_games_stored_mutex.set()
        return True

    def update_genre_database(self, game_data: dict) -> None:
        """
        For each game not in database, request Steam Big Picture API
        to get required data. If changed in the future, the APi call
        will need to be modified.
        
        :param self: Description
        :param game_data: User game data
        :type game_data: dict
        """

        self.getting_genres_mutex.clear()
        games = game_data.get("games", [])
        games_added = set()

        for game in games:
            app_id = game["appid"]
            if (app_id not in self._games_stored):
                # Request steam API
                url = f"https://store.steampowered.com/api/appdetails?appids={app_id}&filters=basic,genres"
                response = requests.get(url)

                if (response.status_code == 200):
                    api_data = response.json()

                    if (not api_data[str(app_id)]["success"]):
                        # Game information unavailable. Don't consider.
                        continue

                    # Get data from JSON
                    name = api_data[str(app_id)]["data"].get("name", "")
                    genres = api_data[str(app_id)]["data"].get("genres", [])
                    formatted_genres = ""
                    for genre in genres:
                        formatted_genres += genre["description"] + ','
                    
                    print(f"Name: {name} | ID: {app_id}")

                    # Thread-safe behavior
                    self.writing_to_database_mutex.wait()
                    self.writing_to_database_mutex.clear()
                    with self._game_database as databsae:
                        try:
                            databsae.insert((app_id, name, formatted_genres))
                            games_added.add(app_id)
                        except sqlite3.IntegrityError as error:
                            # Should not happen but if it does, we aren't checking
                            # properly games stored in the database.
                            print(error)
                            print(f"Exception occurred when writing game " 
                                  f"{app_id},{name},{formatted_genres} to database.")

                    self.writing_to_database_mutex.set()

                    time.sleep(0.75) # Politeness delay
                else:
                    print(f"Request failed with HTTP code {response.status_code}") 

        self.checking_games_stored_mutex.wait()
        self.checking_games_stored_mutex.clear()

        for id in games_added:
            self._games_stored.add(id)

        self.checking_games_stored_mutex.set()
        self.getting_genres_mutex.set()
