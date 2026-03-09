import os
import requests
from .http_client import create_retry_session

class SteamService:
    def __init__(self):
        self.api_key = os.getenv('STEAM_API_KEY')
        self.base_url = 'https://api.steampowered.com'
        self.timeout_seconds = 10
        self.session = create_retry_session()

    def _get_json(self, endpoint: str, params: dict) -> dict:
        response = self.session.get(endpoint, params=params, timeout=self.timeout_seconds)
        response.raise_for_status()
        return response.json()

    def _normalize_steam_id(self, steam_id: str) -> str:
        if not self.api_key:
            raise ValueError("STEAM_API_KEY is missing. Please configure it in your environment.")

        try:
            int(steam_id)
            return str(steam_id)
        except ValueError:
            endpoint = "https://api.steampowered.com/ISteamUser/ResolveVanityURL/v1/"
            params = {
                "key": self.api_key,
                "vanityurl": steam_id,
                "url_type": 1,
            }
            data = self._get_json(endpoint, params)
            if data.get("response", {}).get("success") != 1:
                raise ValueError(
                    "Invalid Steam ID. Please provide a valid custom URL name or 17-digit steamID64."
                )
            return data["response"]["steamid"]
    
    def get_owned_games(self, steam_id):
        steam_id = self._normalize_steam_id(steam_id)

        endpoint = f'{self.base_url}/IPlayerService/GetOwnedGames/v1/'
        params = {
            'key': self.api_key,
            'steamid': steam_id,
            'include_appinfo': 1,
            'include_played_free_games': 1,
            'format': 'json'
        }

        data = self._get_json(endpoint, params)
        return data.get('response', {})
    
    def get_recently_played(self, steam_id):
        steam_id = self._normalize_steam_id(steam_id)

        endpoint = f'{self.base_url}/IPlayerService/GetRecentlyPlayedGames/v1/'
        params = {
            'key': self.api_key,
            'steamid': steam_id,
            'format': 'json'
        }

        data = self._get_json(endpoint, params)
        return data.get('response', {})