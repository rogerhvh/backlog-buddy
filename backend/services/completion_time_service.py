import time
from typing import Optional
from howlongtobeatpy import HowLongToBeat
from concurrent.futures import ThreadPoolExecutor, as_completed

class HLTBService:    
    def __init__(self):
        self.hltb = HowLongToBeat()
        self.cache = {}
    
    def get_completion_time(self, game_name: str) -> Optional[int]:
        """
        Fetch estimated completion time for a game from HowLongToBeat
        Returns None if unable to fetch (graceful failure)
        
        args:
            game_name: Name of the game to search for
            
        returns:
            Estimated hours to complete (main story), or None if not found
        """
        # Check cache first
        if game_name in self.cache:
            result = self.cache[game_name]
            if result:
                print(f"✓ Cache hit for '{game_name}': {result} hours")
            return result
        
        print(f"➜ Searching HowLongToBeat for '{game_name}'...")
        
        try:
            results = self.hltb.search(game_name)
            
            # search() returns a list of results
            if not results or len(results) == 0:
                print(f"⊘ No match for '{game_name}'")
                self.cache[game_name] = None
                return None
            
            # Get first (best) match
            game = results[0]
            completion_time = game.main_story
            
            if completion_time and completion_time > 0:
                hours = int(completion_time)
                print(f"✓ Found '{game_name}': ~{hours}h")
                self.cache[game_name] = hours
                return hours
            else:
                print(f"⊘ No completion time for '{game_name}'")
                self.cache[game_name] = None
                return None
            
        except Exception as e:
            print(f"⊘ Error for '{game_name}': {str(e)[:50]}")
            self.cache[game_name] = None
            return None
    
    def get_completion_times_batch(self, game_names: list) -> dict:
        """
        Fetch completion times for multiple games in parallel
        
        args:
            game_names: List of game names
            
        returns:
            Dictionary mapping game names to completion times (hours) or None
        """
        print(f"\nFetching completion times for {len(game_names)} games (parallel)...\n")
        result = {}
        
        # parallel requests (5 at a time)
        with ThreadPoolExecutor(max_workers=5) as executor:
            future_to_name = {
                executor.submit(self.get_completion_time, name): name 
                for name in game_names
            }
            
            for future in as_completed(future_to_name):
                name = future_to_name[future]
                try:
                    result[name] = future.result()
                except Exception as e:
                    print(f"⊘ Error fetching '{name}': {e}")
                    result[name] = None
        
        print(f"\nBatch processing complete\n")
        return result
