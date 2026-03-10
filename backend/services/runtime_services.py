from services.steam_services import SteamService
from services.reccomendation_service import RecommendationService
from services.profile_service import ProfileService

steam_service = SteamService()
rec_service = RecommendationService()  # index injected by app.py after startup
profile_service = ProfileService()

def set_index(index) -> None:
    rec_service._index = index