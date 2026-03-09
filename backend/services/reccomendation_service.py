# backend/services/recommendation_service.py

import sqlite3
from data.game_database import GameDatabase
import requests
import time
from threading import Lock, Thread
from requests import RequestException
from .completion_time_service import HLTBService
from .http_client import create_retry_session

class RecommendationService:

    def __init__(self):
        self.hltb_service = HLTBService()
        self._game_database: GameDatabase = GameDatabase()
        self._game_database_temp: GameDatabase = GameDatabase(temp=True)
        self.timeout_seconds = 10
        self.session = create_retry_session()
        self._indexing_lock = Lock()
        with self._game_database as database:
            database.create_database()
            self._games_stored: set[int] = database.get_all_games_stored()
        with self._game_database_temp as database:
            database.create_database()
            self._games_stored_temp: set[int] = database.get_all_games_stored()

    def _fetch_json(self, url: str):
        try:
            response = self.session.get(url, timeout=self.timeout_seconds)
            response.raise_for_status()
            return response.json()
        except (RequestException, ValueError):
            return None

    def start_genre_indexing_if_needed(self, game_data: dict, daemon: bool = True) -> str:
        if self.check_if_games_stored(game_data):
            return "up_to_date"

        if not self._indexing_lock.acquire(blocking=False):
            return "in_progress"

        try:
            thread = Thread(
                target=self.update_genre_database,
                args=(game_data,),
                daemon=daemon,
            )
            thread.start()
            return "started"
        except Exception:
            self._indexing_lock.release()
            raise
    
    def rank_games(
        self,
        games,
        time_available=120,
        preferred_genres=None,
        min_playtime_hours=None,
        max_playtime_hours=None
    ):
        """        
        args:
            games: List of game dictionaries from Steam API
            time_available: user's available time in minutes
        """
        preferred_genres_set = {
            genre.strip().lower() for genre in (preferred_genres or []) if genre and genre.strip()
        }

        scored_games = []
        with self._game_database as database:
            for game in games:
                genres = database.get_genre(game["appid"])
                completion_time_hours = database.get_ttc(game["appid"])

                game_with_data = {
                    **game,
                    'genres': genres,
                    'completion_time_hours': completion_time_hours
                }

                if not self._matches_playtime_preferences(
                    game_with_data,
                    min_playtime_hours,
                    max_playtime_hours
                ):
                    continue

                score = self._calculate_score(
                    game_with_data,
                    time_available,
                    preferred_genres_set
                )

                scored_games.append({
                    **game_with_data,
                    'recommendation_score': score
                })
        
        # Re-sort with updated scores
        scored_games.sort(key=lambda x: x['recommendation_score'], reverse=True)
        return scored_games
    
    # tentative scoring function, can refine later
    def _calculate_score(self, game, time_available, preferred_genres_set=None):
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

        # factor 6: preferred genre matching
        if preferred_genres_set:
            game_genres = self._normalize_genres(game.get('genres', ''))
            if game_genres and game_genres.intersection(preferred_genres_set):
                score += 25
            elif game_genres:
                score -= 5
        
        return score

    def _normalize_genres(self, genres: str) -> set[str]:
        if not genres:
            return set()

        normalized = {
            genre.strip().lower()
            for genre in str(genres).split(',')
            if genre.strip()
        }

        normalized.discard('no genre information.')
        normalized.discard('no genre information')
        return normalized

    def _matches_playtime_preferences(self, game, min_playtime_hours, max_playtime_hours) -> bool:
        completion_time_hours = game.get('completion_time_hours')

        if completion_time_hours is None:
            return True

        if min_playtime_hours is not None and completion_time_hours < min_playtime_hours:
            return False

        if max_playtime_hours is not None and completion_time_hours > max_playtime_hours:
            return False

        return True
    
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
            app_id = game.get("appid")
            if app_id is None:
                continue
            if app_id not in self._games_stored and app_id not in self._games_stored_temp:
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

        games = game_data.get("games", [])
        games_added = set()

        try:
            for game in games:
                app_id = game.get("appid")
                if app_id is None:
                    continue

                if app_id in self._games_stored or app_id in self._games_stored_temp:
                    continue

                steam_url = f"https://store.steampowered.com/api/appdetails?appids={app_id}&filters=basic,genres"
                steam_spy_url = f"https://steamspy.com/api.php?request=appdetails&appid={app_id}"

                steam_api_data = self._fetch_json(steam_url)
                if not steam_api_data:
                    continue

                app_data = steam_api_data.get(str(app_id), {})
                if not app_data.get("success"):
                    continue

                steam_spy_api_data = self._fetch_json(steam_spy_url) or {}

                completion_time = self.hltb_service.get_completion_time(game.get("name", ""), app_id)

                steam_data = app_data.get("data", {})
                name = steam_data.get("name", "") or ""
                header_image = steam_data.get("header_image")
                genres = steam_data.get("genres", [])
                genres_steam_spy = steam_spy_api_data.get("tags", {})

                normalized_genres = {
                    entry["description"].lower()
                    for entry in genres
                    if isinstance(entry, dict) and entry.get("description")
                }

                if isinstance(genres_steam_spy, dict):
                    for genre in genres_steam_spy.keys():
                        normalized_genres.add(str(genre).lower())

                formatted_genres = ','.join(sorted(normalized_genres))

                with self._game_database_temp as database:
                    try:
                        database.insert((app_id, name, formatted_genres, header_image, completion_time))
                        games_added.add(app_id)
                    except sqlite3.IntegrityError:
                        continue

                time.sleep(0.5)
        finally:
            self._games_stored_temp = self._games_stored_temp | games_added
            if self._indexing_lock.locked():
                self._indexing_lock.release()
