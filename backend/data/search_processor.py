
from math import log
from pathlib import Path
from data.game_database import GameDatabse

class SearchProcessor:

    @staticmethod
    def get_tag_idf(num_tags: int, index_path: Path) -> dict[str: float]:
        """
        In the cosine similarity formula, this returns the IDF values 
        """

        res = dict()
        with index_path.open('r') as f:
            for line in f:
                tag, games = line.split(':')
                res[tag] = log(num_tags / len(games.split(',')))
        
        return res
    
    @staticmethod
    def write_tag_idf(tag_idf: dict[str: float], tag_path: Path) -> None:
        """
        Writes to tag vector data to store on disk.
        """
        with tag_path.open('w') as f:
            for key, value in tag_idf.items():
                f.write(f"{key}:{value}\n")
    
    @staticmethod
    def update_game_vector(tag_idf: dict[str, float], game_db: GameDatabse) -> None:
        """
        Update IDF values if we add more data.
        """
        
        pass