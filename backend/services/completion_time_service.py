import time
from typing import Optional, Tuple
from howlongtobeatpy import HowLongToBeat
from concurrent.futures import ThreadPoolExecutor, as_completed
from database.database import UserProfileDatabase

class HLTBService:    
    def __init__(self):
        self.hltb = HowLongToBeat()
        self.cache = {}  # In-memory cache for this session
        self.db = None   # Database connection (lazy loaded)
    
    def _get_db(self):
        """Lazy load database connection."""
        if self.db is None:
            self.db = UserProfileDatabase()
            self.db._connect_to_db()
            self.db.create_database()
        return self.db
    
    def get_completion_time(self, game_name: str, appid: Optional[int] = None) -> Optional[int]:
        """
        Fetch estimated completion time for a game from HowLongToBeat.
        First checks in-memory cache, then database, then API.
        Returns None if unable to fetch (graceful failure).
        """
        # Check in-memory cache first
        if game_name in self.cache:
            result = self.cache[game_name]
            if result:
                print(f"✓ Cache hit for '{game_name}': {result} hours")
            return result
        
        # Check database if appid provided
        if appid:
            try:
                db = self._get_db()
                db_result = db.get_completion_time(appid)
                if db_result is not None:
                    print(f"✓ Database hit for '{game_name}': {db_result} hours")
                    self.cache[game_name] = db_result
                    return db_result
            except Exception as e:
                print(f"⊘ Database lookup error for '{game_name}': {str(e)[:50]}")
        
        print(f"➜ Searching HowLongToBeat for '{game_name}'...")
        
        try:
            results = self.hltb.search(game_name)
            
            # search() returns a list of results
            if not results or len(results) == 0:
                print(f"⊘ No match for '{game_name}'")
                self.cache[game_name] = None
                if appid:
                    try:
                        db = self._get_db()
                        db.store_completion_time(appid, game_name, None)
                    except Exception as e:
                        print(f"⊘ Error storing None for '{game_name}': {e}")
                return None
            
            # Get best match
            game = results[0]
            completion_time = game.main_story
            
            if completion_time and completion_time > 0:
                hours = int(completion_time)
                print(f"✓ Found '{game_name}': ~{hours}h")
                self.cache[game_name] = hours
                
                # Store in database
                if appid:
                    try:
                        db = self._get_db()
                        db.store_completion_time(appid, game_name, hours)
                    except Exception as e:
                        print(f"⊘ Error storing completion time for '{game_name}': {e}")
                
                return hours
            else:
                print(f"⊘ No completion time for '{game_name}'")
                self.cache[game_name] = None
                if appid:
                    try:
                        db = self._get_db()
                        db.store_completion_time(appid, game_name, None)
                    except Exception as e:
                        print(f"⊘ Error storing None for '{game_name}': {e}")
                return None
            
        except Exception as e:
            print(f"⊘ Error for '{game_name}': {str(e)[:50]}")
            self.cache[game_name] = None
            return None
    
    def get_completion_times_batch(self, games: list) -> dict:
        """
        Fetch completion times for multiple games (appid, game_name tuples or just names).
        Uses database cache + parallel API requests for misses.
        """
        print(f"\nFetching completion times for {len(games)} games (with database cache)...\n")
        result = {}
        games_to_fetch = []
        
        # Process as tuples (appid, game_name) or just names
        game_map = {}
        for game in games:
            if isinstance(game, tuple):
                appid, game_name = game
                game_map[game_name] = appid
            else:
                game_map[game] = None
        
        # Check database for any cached results
        for game_name, appid in game_map.items():
            if game_name in self.cache:
                result[game_name] = self.cache[game_name]
            elif appid:
                try:
                    db = self._get_db()
                    db_result = db.get_completion_time(appid)
                    if db_result is not None:
                        print(f"✓ Database hit for '{game_name}': {db_result}h")
                        result[game_name] = db_result
                        self.cache[game_name] = db_result
                    else:
                        games_to_fetch.append((game_name, appid))
                except Exception as e:
                    print(f"⊘ Database error for '{game_name}': {str(e)[:50]}")
                    games_to_fetch.append((game_name, appid))
            else:
                games_to_fetch.append((game_name, None))
        
        # Fetch missing games in parallel
        if games_to_fetch:
            print(f"Fetching {len(games_to_fetch)} games from API...\n")
            with ThreadPoolExecutor(max_workers=5) as executor:
                future_to_game = {
                    executor.submit(self.get_completion_time, name, appid): (name, appid)
                    for name, appid in games_to_fetch
                }
                
                for future in as_completed(future_to_game):
                    name, appid = future_to_game[future]
                    try:
                        result[name] = future.result()
                    except Exception as e:
                        print(f"⊘ Error fetching '{name}': {e}")
                        result[name] = None
        
        print(f"Batch processing complete\n")
        return result
    
    def refresh_stale_data(self, max_age_days: int = 30, limit: int = 10) -> None:
        """
        Refreshes completion time data older than max_age_days.
        Useful for background updates of game data.
        """
        try:
            db = self._get_db()
            stale_games = db.get_stale_completion_times(max_age_days)
            
            if not stale_games:
                print("No stale completion time data to refresh")
                return
            
            games_to_refresh = stale_games[:limit]
            print(f"Refreshing {len(games_to_refresh)} stale entries (older than {max_age_days} days)...")
            
            for appid, game_name in games_to_refresh:
                print(f"Refreshing '{game_name}'...")
                self.get_completion_time(game_name, appid)
            
            print("Stale data refresh complete\n")
        except Exception as e:
            print(f"Error refreshing stale data: {e}")
    
    def __del__(self):
        """Clean up database connection on exit."""
        if self.db:
            try:
                self.db._close_connection()
            except:
                pass
