# backend/routes/game_routes.py
from flask import Blueprint, jsonify, request
from services.runtime_services import steam_service, rec_service, profile_service

game_bp = Blueprint('games', __name__)

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

@game_bp.route('/recommendations/<user_id>', methods=['POST'])
def get_recommendations(user_id):
    try:
        profile = profile_service.get_profile_by_user_id(user_id)
        if not profile:
            return jsonify({
                "success": False,
                "error": "Profile not found. Please create a profile before requesting recommendations."
            }), 404

        steam_id = profile.steam_id
        if not steam_id:
            return jsonify({
                "success": False,
                "error": "Profile is missing a Steam ID. Please update your profile first."
            }), 400

        # get context from request body
        context = request.json or {}
        time_available = context.get('time_available', 120)  # minutes
        
        library = steam_service.get_owned_games(steam_id)
        rec_service.start_genre_indexing_if_needed(library)
        
        # generate recommendations
        recommendations = rec_service.rank_games(
            library.get('games', []),
            time_available=time_available,
            preferred_genres=profile.preferred_genres,
            min_playtime_hours=profile.min_playtime_hours,
            max_playtime_hours=profile.max_playtime_hours
        )
        
        return jsonify({
            "success": True,
            "recommendations": recommendations[:10]
        }), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500