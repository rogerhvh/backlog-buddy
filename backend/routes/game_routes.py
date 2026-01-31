# backend/routes/game_routes.py
from flask import Blueprint, jsonify, request
from services.steam_services import SteamService
from services.reccomendation_service import RecommendationService
import threading

game_bp = Blueprint('games', __name__)
steam_service = SteamService()
rec_service = RecommendationService()

@game_bp.route('/library/<steam_id>', methods=['GET'])
def get_library(steam_id):
    try:
        library = steam_service.get_owned_games(steam_id)
        return jsonify({
            "success": True,
            "game_count": library.get('game_count', 0),
            "games": library.get('games', [])
        }), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@game_bp.route('/recommendations/<steam_id>', methods=['POST'])
def get_recommendations(steam_id):
    try:
        # get context from request body
        context = request.json or {}
        time_available = context.get('time_available', 120)  # minutes
        
        library = steam_service.get_owned_games(steam_id)
        use_genres = rec_service.check_if_games_stored(library)
        if (not use_genres and rec_service.getting_genres_mutex.is_set()):

            # If there is a background thread doing work, ignore
            # any future requests to start new threads 

            # NOTE: If an new user inputs their data, then we ignore their request.
            # if the mutex is set. Should we queue data instead? Would have to check
            # genre list again so we don't queue with expired information.

            thread = threading.Thread(target=rec_service.update_genre_database, args=(library,))
            thread.start()
        
        # generate recommendations
        recommendations = rec_service.rank_games(
            library.get('games', []),
            time_available=time_available
        )
        
        return jsonify({
            "success": True,
            "recommendations": recommendations[:10]
        }), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500