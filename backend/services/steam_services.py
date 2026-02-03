# backend/services/steam_service.py
import requests
import os

class SteamService:
    def __init__(self):
        self.api_key = os.getenv('STEAM_API_KEY')
        self.base_url = 'https://api.steampowered.com'
    
    def get_owned_games(self, steam_id):
        try:
            # Say the user inputed an ID 765XXX..
            _ = int(steam_id)
        except ValueError:
            # Assume the user has entered a string
            # https://partner.steamgames.com/doc/webapi/isteamuser
            endpoint = f"https://api.steampowered.com/ISteamUser/ResolveVanityURL/v1/"
            params = {
                "key": self.api_key,
                "vanityurl": steam_id,
                "url_type": 1,
            }

            response = requests.get(endpoint, params=params)
            response.raise_for_status() 

            data = response.json()
        
            # Success 42 = Fail, 1 = OK
            match data["response"].get("success", 42):
                case 1: pass
                case 42: raise Exception("Not provided a valid steam ID. Please enter your " \
                                         "custom ID or your 17-digit permanent account " \
                                         "numeric identifier")
            
            steam_id = data["response"]["steamid"]

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