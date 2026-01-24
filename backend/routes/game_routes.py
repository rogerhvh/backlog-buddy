# backend/routes/game_routes.py
from flask import Blueprint, jsonify, request
from services.steam_services import SteamService
from services.reccomendation_service import RecommendationService

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