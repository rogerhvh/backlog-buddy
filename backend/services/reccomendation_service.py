# backend/services/recommendation_service.py

import heapq
import sqlite3
from pathlib import Path
from data.game_database import GameDatabase
import requests
import time
from threading import Lock, Thread
from requests import RequestException
from .completion_time_service import HLTBService
from .http_client import create_retry_session

# Mirrors INDEX_NAME in data/index.py
INDEX_PATH = Path("./data/index.backlog_buddy")

# Number of top playtime-scored games whose genres form the taste profile
TOP_N = 10


class RecommendationService:

    def __init__(self, index=None):
        self.hltb_service = HLTBService()
        self._game_database: GameDatabase = GameDatabase()
        self._game_database_temp: GameDatabase = GameDatabase(temp=True)
        self.timeout_seconds = 10
        self.session = create_retry_session()
        self._indexing_lock = Lock()
        self._index = index
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
        games: list[dict],
        time_available: int = 120,
        preferred_genres=None,
        min_playtime_hours=None,
        max_playtime_hours=None,
    ) -> list[dict]:
        """
        Pass 1 — Playtime relevance (no DB needed)
            Score every game by playtime signals only using a min-heap of
            size TOP_N to identify the top N most-engaged-with games in
            O(N log TOP_N) without sorting the full library.

        Pass 2 — Taste profile construction (TOP_N DB reads)
            Seed the taste profile with any preferred_genres from the user's
            profile first — these are guaranteed to influence scoring
            regardless of playtime history. Then add genres derived from the
            top N played games so the profile also reflects actual behaviour.
            Falls back to playtime-only ranking if the DB is still empty
            (background indexing thread not yet finished).

        Pass 3 — Index lookup + genre/TTC scoring
            Read index.backlog_buddy once. For every tag in the taste
            profile, collect candidate appids from the posting list,
            restricting to games in this user's library. Score each
            candidate by genre overlap ratio + TTC fit + light playtime
            familiarity bonus. Apply min/max playtime filters if set.
            Return top 20.
        """
        if not games:
            return []

        time_available_hours = time_available / 60

        # ------------------------------------------------------------------
        # Pass 1: min-heap to find top TOP_N games by playtime score
        # ------------------------------------------------------------------
        library_by_id: dict[int, dict] = {}
        top_heap: list[tuple[float, int]] = []  # (score, appid)

        for game in games:
            app_id = game.get("appid")
            if app_id is None:
                continue
            library_by_id[app_id] = game
            score = self._playtime_score(game)

            if len(top_heap) < TOP_N:
                heapq.heappush(top_heap, (score, app_id))
            elif score > top_heap[0][0]:
                heapq.heapreplace(top_heap, (score, app_id))

        top_ids: list[int] = [app_id for _, app_id in top_heap]

        # ------------------------------------------------------------------
        # Pass 2: build taste profile weighted by playtime
        # ------------------------------------------------------------------
        # taste_profile maps tag -> weight, reflecting how much time the user
        # has actually invested in games of that genre.
        #
        # Sources:
        #   preferred_genres from profile  → base weight of (playtime_hours + 1)
        #                                    for every top-10 game that shares
        #                                    the tag, +1 if no top-10 game does.
        #                                    Explicit preferences are seeded
        #                                    first so they always contribute.
        #   genres from top N played games → += playtime_hours for that game
        #
        # Example: Yu-Gi-Oh (230h, tags: "trading card game, anime")
        #   "trading card game" += 230, "anime" += 230
        # If "anime" is also a preferred genre it gets an additional +1 seed,
        # so it accumulates more weight than a non-preferred tag with equal
        # playtime.
        #
        # Duplicate entries in preferred_genres are intentionally collapsed —
        # listing "anime" six times is treated the same as listing it once
        # since the signal strength comes from playtime, not repetition.
        taste_profile: dict[str, float] = {}

        # Seed preferred genres with a small base weight so they are always
        # represented even if none of the top-10 games share the tag.
        preferred_set = self._normalize_genres(','.join(preferred_genres or []))
        for tag in preferred_set:
            taste_profile[tag] = taste_profile.get(tag, 0) + 1.0

        # Weight each tag from the top N games by that game's playtime in
        # hours. Preferred tags that also appear here accumulate more weight
        # than non-preferred tags with the same playtime.
        with self._game_database as database:
            for app_id in top_ids:
                game_data = library_by_id[app_id]
                playtime_hours = game_data.get('playtime_forever', 0) / 60
                genre_str = database.get_genre(app_id)
                for tag in self._normalize_genres(genre_str):
                    # Preferred tags get a 2× multiplier on their playtime
                    # contribution to reflect the explicit user signal.
                    multiplier = 2.0 if tag in preferred_set else 1.0
                    taste_profile[tag] = (
                        taste_profile.get(tag, 0) + playtime_hours * multiplier
                    )

        # DB empty — background thread hasn't finished yet. Return playtime
        # ranking immediately so the user always gets a result.
        if not taste_profile:
            return self._playtime_fallback(games, min_playtime_hours, max_playtime_hours)

        # ------------------------------------------------------------------
        # Pass 3: single index scan → per-candidate DB reads → final sort
        # ------------------------------------------------------------------
        # candidates maps appid -> accumulated tag weight (sum of
        # taste_profile[tag] for every tag the game shares with the profile).
        candidates: dict[int, float] = {}

        if INDEX_PATH.exists() and INDEX_PATH.stat().st_size > 0:
            with INDEX_PATH.open('r') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    tag, ids_str = line.split(':', 1)
                    tag_weight = taste_profile.get(tag, 0)
                    if tag_weight == 0:
                        continue
                    for id_str in ids_str.split(','):
                        id_str = id_str.strip()
                        if not id_str:
                            continue
                        app_id = int(id_str)
                        if app_id in library_by_id:
                            candidates[app_id] = candidates.get(app_id, 0) + tag_weight

        if not candidates:
            return self._playtime_fallback(games, min_playtime_hours, max_playtime_hours)

        scored: list[dict] = []

        with self._game_database as database:
            for app_id, genre_overlap in candidates.items():
                game = library_by_id[app_id]
                ttc = database.get_ttc(app_id)
                genre_str = database.get_genre(app_id)

                game_with_data = {
                    **game,
                    'genres': genre_str,
                    'completion_time_hours': ttc,
                }

                if not self._matches_playtime_preferences(
                    game_with_data, min_playtime_hours, max_playtime_hours
                ):
                    continue

                final_score = self._recommendation_score(
                    game=game,
                    genre_overlap=genre_overlap,
                    ttc=ttc,
                    time_available_hours=time_available_hours,
                )

                scored.append({
                    **game_with_data,
                    'recommendation_score': final_score,
                })

        scored.sort(key=lambda x: x['recommendation_score'], reverse=True)
        return scored[:20]

    # -------------------------------------------------------------------------
    # Scoring helpers
    # -------------------------------------------------------------------------

    def _playtime_score(self, game: dict) -> float:
        """
        Pass 1: playtime-only score. No DB access.

        Factor 1 — recent playtime:  normalised so 120 min recent = 20 pts max
        Factor 2 — total playtime:   investment signal, capped at 100 h → 30 pts
        Factor 3 — started but not finished (0 < playtime < 5 h) → +20 pts
        """
        score = 0.0
        playtime_2weeks  = game.get('playtime_2weeks', 0)
        playtime_forever = game.get('playtime_forever', 0)

        score += min(playtime_2weeks / 120, 1.0) * 20.0
        score += min(playtime_forever / 60, 100) * 0.3
        if 0 < playtime_forever < 300:
            score += 20.0
        return score

    def _recommendation_score(
        self,
        game: dict,
        genre_overlap: float,
        ttc: int | None,
        time_available_hours: float,
    ) -> float:
        """
        Pass 3: final score combining genre match + TTC fit.

        Factor 1 — playtime-weighted genre overlap (uncapped)
                    genre_overlap is the sum of taste_profile weights for every
                    tag the game shares with the profile. Each tag's weight
                    reflects total hours played across top-10 games with that
                    genre, doubled for tags that are also in preferred_genres.
                    A game matching a genre the user has 200h in scores far
                    higher than one matching a genre they only played for 5h.
        Factor 2 — TTC fit:  fits perfectly → +30, within 1.5× → +15, too long → -5
        Factor 3 — light playtime familiarity bonus, max 10 pts
        """
        score = 0.0

        # Normalise playtime-weighted overlap: divide by 10 so that
        # 100h of genre playtime contributes ~10pts, 300h contributes ~30pts.
        # This keeps genre scores in the same order of magnitude as TTC
        # bonuses (+30/+15) while still rewarding heavily-played genres.
        score += genre_overlap / 10.0

        if ttc is not None and ttc > 0:
            if ttc <= time_available_hours:
                score += 30.0
            elif ttc <= time_available_hours * 1.5:
                score += 15.0
            else:
                score -= 5.0

        playtime_forever = game.get('playtime_forever', 0)
        score += min(playtime_forever / 60, 100) * 0.1

        return score

    def _playtime_fallback(
        self,
        games: list[dict],
        min_playtime_hours=None,
        max_playtime_hours=None,
    ) -> list[dict]:
        """
        Returned when the DB/index is not yet populated.
        Sorts by playtime score and still applies playtime filters where data
        is available, so the response shape is always consistent.
        """
        scored = []
        for game in games:
            game_with_data = {
                **game,
                'genres': 'No genre information.',
                'completion_time_hours': None,
            }
            if not self._matches_playtime_preferences(
                game_with_data, min_playtime_hours, max_playtime_hours
            ):
                continue
            scored.append({
                **game_with_data,
                'recommendation_score': self._playtime_score(game),
            })
        scored.sort(key=lambda x: x['recommendation_score'], reverse=True)
        return scored[:20]

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
            # Merge games_temp.db into games.db and rebuild the index so
            # rank_games can use genre data immediately on the next request.
            if self._index is not None and games_added:
                self._index.update_index()
                # Refresh _games_stored so check_if_games_stored sees the
                # newly promoted games on the next call.
                with self._game_database as database:
                    self._games_stored = database.get_all_games_stored()
            if self._indexing_lock.locked():
                self._indexing_lock.release()