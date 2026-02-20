# backend/models.py
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class Game:
    appid: int
    name: str
    playtime_forever: int  # minutes
    playtime_2weeks: int = 0
    img_icon_url: str = ""
    img_logo_url: str = ""
    completion_time_hours: Optional[int] = None  # estimated hours to complete
    
    @property
    def hours_played(self):
        return round(self.playtime_forever / 60, 1)
    
    @classmethod
    def from_steam_api(cls, data: dict):
        return cls(
            appid=data.get('appid'),
            name=data.get('name', 'Unknown'),
            playtime_forever=data.get('playtime_forever', 0),
            playtime_2weeks=data.get('playtime_2weeks', 0),
            img_icon_url=data.get('img_icon_url', ''),
            img_logo_url=data.get('img_logo_url', ''),
            completion_time_hours=None
        )

@dataclass
class UserContext:
    time_available: int  # minutes
    hardware_tier: str = "mid"  # low, mid, high
    preferred_genres: List[str] = None
    
    def __post_init__(self):
        if self.preferred_genres is None:
            self.preferred_genres = []