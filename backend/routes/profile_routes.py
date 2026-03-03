# backend/routes/profile_routes.py
from flask import Blueprint, jsonify, request
from services.runtime_services import profile_service, steam_service, rec_service
import threading

profile_bp = Blueprint('profiles', __name__)

@profile_bp.route('/profile', methods=['POST'])
def create_profile():
    """Create a new user profile."""
    try:
        data = request.json or {}
        user_id = data.get('user_id')
        steam_id = data.get('steam_id')
        preferred_genres = data.get('preferred_genres', [])
        min_playtime_hours = data.get('min_playtime_hours')
        max_playtime_hours = data.get('max_playtime_hours')
        
        if not user_id or not steam_id:
            return jsonify({"success": False, "error": "user_id and steam_id are required"}), 400
        
        profile = profile_service.create_profile(
            user_id, steam_id, preferred_genres, min_playtime_hours, max_playtime_hours
        )

        indexing_status = "up_to_date"
        try:
            library = steam_service.get_owned_games(profile.steam_id)
            needs_indexing = not rec_service.check_if_games_stored(library)
            if needs_indexing:
                if rec_service.getting_genres_mutex.is_set():
                    thread = threading.Thread(
                        target=rec_service.update_genre_database,
                        args=(library,),
                        daemon=True
                    )
                    thread.start()
                    indexing_status = "started"
                else:
                    indexing_status = "in_progress"
        except Exception:
            indexing_status = "failed"
        
        return jsonify({
            "success": True,
            "genre_indexing_status": indexing_status,
            "profile": {
                "user_id": profile.user_id,
                "steam_id": profile.steam_id,
                "preferred_genres": profile.preferred_genres,
                "min_playtime_hours": profile.min_playtime_hours,
                "max_playtime_hours": profile.max_playtime_hours,
                "creation_date": profile.creation_date,
                "last_updated": profile.last_updated
            }
        }), 201
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@profile_bp.route('/profile/<user_id>', methods=['GET'])
def get_profile(user_id):
    """Retrieve a profile by user_id."""
    try:
        profile = profile_service.get_profile_by_user_id(user_id)
        
        if not profile:
            return jsonify({"success": False, "error": "Profile not found"}), 404
        
        return jsonify({
            "success": True,
            "profile": {
                "user_id": profile.user_id,
                "steam_id": profile.steam_id,
                "preferred_genres": profile.preferred_genres,
                "min_playtime_hours": profile.min_playtime_hours,
                "max_playtime_hours": profile.max_playtime_hours,
                "creation_date": profile.creation_date,
                "last_updated": profile.last_updated
            }
        }), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@profile_bp.route('/profile/<user_id>', methods=['PUT'])
def update_profile(user_id):
    """Update a user profile."""
    try:
        data = request.json or {}
        steam_id = data.get('steam_id')
        preferred_genres = data.get('preferred_genres')
        min_playtime_hours = data.get('min_playtime_hours')
        max_playtime_hours = data.get('max_playtime_hours')
        
        profile = profile_service.update_profile(
            user_id, steam_id, preferred_genres, min_playtime_hours, max_playtime_hours
        )
        
        return jsonify({
            "success": True,
            "profile": {
                "user_id": profile.user_id,
                "steam_id": profile.steam_id,
                "preferred_genres": profile.preferred_genres,
                "min_playtime_hours": profile.min_playtime_hours,
                "max_playtime_hours": profile.max_playtime_hours,
                "creation_date": profile.creation_date,
                "last_updated": profile.last_updated
            }
        }), 200
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@profile_bp.route('/profile/<user_id>', methods=['DELETE'])
def delete_profile(user_id):
    """Delete a user profile."""
    try:
        profile_service.delete_profile(user_id)
        
        return jsonify({
            "success": True,
            "message": "Profile deleted successfully"
        }), 200
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@profile_bp.route('/profile/steam/<steam_id>', methods=['GET'])
def get_profile_by_steam(steam_id):
    """Retrieve a profile by steam_id."""
    try:
        profile = profile_service.get_profile_by_steam_id(steam_id)
        
        if not profile:
            return jsonify({"success": False, "error": "Profile not found"}), 404
        
        return jsonify({
            "success": True,
            "profile": {
                "user_id": profile.user_id,
                "steam_id": profile.steam_id,
                "preferred_genres": profile.preferred_genres,
                "min_playtime_hours": profile.min_playtime_hours,
                "max_playtime_hours": profile.max_playtime_hours,
                "creation_date": profile.creation_date,
                "last_updated": profile.last_updated
            }
        }), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
