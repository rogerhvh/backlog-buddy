# backend/services/steam_service.py
import requests
import os

class SteamService:
    def __init__(self):
        self.api_key = os.getenv('STEAM_API_KEY')
        self.base_url = 'https://api.steampowered.com'
    
    def get_owned_games(self, steam_id):
        endpoint = f'{self.base_url}/IPlayerService/GetOwnedGames/v1/'
        params = {
            'key': self.api_key,
            'steamid': steam_id,
            'include_appinfo': 1,
            'include_played_free_games': 1,
            'format': 'json'
        }
        
        response = requests.get(endpoint, params=params)
        response.raise_for_status()
        
        data = response.json()
        return data.get('response', {})
    
    def get_recently_played(self, steam_id):
        endpoint = f'{self.base_url}/IPlayerService/GetRecentlyPlayedGames/v1/'
        params = {
            'key': self.api_key,
            'steamid': steam_id,
            'format': 'json'
        }
        
        response = requests.get(endpoint, params=params)
        response.raise_for_status()
        
        data = response.json()
        return data.get('response', {})