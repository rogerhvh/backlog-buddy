
from math import log
from pathlib import Path
from data.game_database import GameDatabase

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
    def update_l2_norm(tag_idf: dict[str, float], game_db: GameDatabase) -> None:
        """
        Update IDF values if we add more data. Calculates L2 norm
        as seen in the denominator of the cosine similarity equation.
        """
        
        with game_db as database:
            for id, _, genres, _ in database.get_all_data():
                genres = genres.split(',')

                l2_norm = 0
                for genre in genres:
                    l2_norm += tag_idf[genre] ** 2
                
                l2_norm = l2_norm ** 0.5
                game_db.update_idf(id, l2_norm)