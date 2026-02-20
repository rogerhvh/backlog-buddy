# backend/services/recommendation_service.py
from .completion_time_service import HLTBService

class RecommendationService:
    def __init__(self):
        self.hltb_service = HLTBService()
    
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
            scored_games.append({
                **game,
                'recommendation_score': score
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
