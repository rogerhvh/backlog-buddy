# backend/services/recommendation_service.py

import sqlite3
from data.game_database import GameDatabase
import requests
import time
from threading import Event
from .completion_time_service import HLTBService

class RecommendationService:

    def __init__(self):
        self.hltb_service = HLTBService()
        self._game_database: GameDatabase = GameDatabase()
        self._game_database_temp: GameDatabase = GameDatabase(temp=True)
        with self._game_database as database:
            database.create_database()
            self._games_stored: set[int] = database.get_all_games_stored()
        with self._game_database_temp as database:
            database.create_database()
            self._games_stored_temp: set[int] = database.get_all_games_stored()
        
        self.getting_genres_mutex = Event()        # Mutex for background thread running
        self.getting_genres_mutex.set()
    
    def rank_games(self, games, time_available=120):
        """        
        args:
            games: List of game dictionaries from Steam API
            time_available: user's available time in minutes
        """
        scored_games = []
        
        # Score all games first with other factors
        for game in games:
            score = self._calculate_score(game, time_available)

            # self.writing_to_database_mutex.wait()
            # self.writing_to_database_mutex.clear()
            with self._game_database as database:
                genre = database.get_genre(game["appid"])
            # self.writing_to_database_mutex.set()

            scored_games.append({
                **game,
                'recommendation_score': score,
                'genres': genre
            })
        
        # Sort to identify top games
        scored_games.sort(key=lambda x: x['recommendation_score'], reverse=True)
        
        # Only fetch completion times for top 20 games (speeds up significantly)
        top_games = scored_games[:20]
        top_game_names = [game['name'] for game in top_games]
        completion_times = self.hltb_service.get_completion_times_batch(top_game_names)
        
        # Add completion time data to top games
        for game in top_games:
            game['completion_time_hours'] = completion_times.get(game['name'])
            # Recalculate score with completion time bonus
            game['recommendation_score'] = self._calculate_score(game, time_available)
        
        # Re-sort with updated scores
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
        
        # factor 4: completion time matching (NEW)
        completion_time_hours = game.get('completion_time_hours')
        if completion_time_hours:
            time_available_hours = time_available / 60
            
            # strong bonus if game can be completed in available time
            if completion_time_hours <= time_available_hours:
                score += 30
            # moderate bonus if game is close to completable
            elif completion_time_hours <= time_available_hours * 1.5:
                score += 15
            # small penalty for games too long for available time
            else:
                score -= 5
        
        # factor 5: time availability match for short sessions
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


        for game in games:
            if (game["appid"] not in self._games_stored):
                return False
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
            if (app_id not in self._games_stored and app_id not in self._games_stored_temp):
                # Request steam API
                steam_url = f"https://store.steampowered.com/api/appdetails?appids={app_id}&filters=basic,genres"
                steam_spy_url = f"https://steamspy.com/api.php?request=appdetails&appid={app_id}"
                steam_response = requests.get(steam_url)
                steam_spy_response = requests.get(steam_spy_url)

                if (steam_response.status_code == 200 and steam_spy_response.status_code == 200):
                    steam_api_data = steam_response.json()
                    steam_spy_api_data = steam_spy_response.json()

                    if (not steam_api_data[str(app_id)]["success"]):
                        # Game information unavailable. Don't consider.
                        continue

                    # Get data from JSON
                    name = steam_api_data[str(app_id)]["data"].get("name", "")
                    genres = steam_api_data[str(app_id)]["data"].get("genres", [])
                    genres_steam_spy = steam_spy_api_data.get("tags")
                    print(genres_steam_spy)

                    genres = set([i["description"].lower() for i in genres]) # Normalization
                    print(genres)

                    if (genres_steam_spy):
                        for genre in genres_steam_spy.keys():
                            genres.add(genre.lower())

                    formatted_genres = ""
                    for genre in genres:
                        formatted_genres += genre + ','
                    
                    # Thread-safe behavior
                    with self._game_database_temp as database:
                        try:
                            database.insert((app_id, name, formatted_genres))
                            games_added.add(app_id)
                        except sqlite3.IntegrityError as error:
                            # Should not happen but if it does, we aren't checking
                            # properly games stored in the database.
                            print(error)
                            print(f"Exception occurred when writing game " 
                                  f"{app_id},{name},{formatted_genres} to database.")

                    time.sleep(0.5) # Politeness delay
                else:
                    print(f"Request failed. \n\tSteam API: {steam_response.status_code}\n\tSteam Spy API: {steam_spy_response.status_code}") 

        self.getting_genres_mutex.set()
