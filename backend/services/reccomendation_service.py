# backend/services/recommendation_service.py
class RecommendationService:
    def rank_games(self, games, time_available=120):
        """        
        args:
            games: List of game dictionaries from Steam API
            time_available: user's available time in minutes
        """
        scored_games = []
        
        for game in games:
            score = self._calculate_score(game, time_available)
            scored_games.append({
                **game,
                'recommendation_score': score
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
