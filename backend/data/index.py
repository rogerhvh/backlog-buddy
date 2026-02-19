
from pathlib import Path
from game_database import GameDatabse
from typing import Self

class TagPosting:
    """
    Class that represents a tag and its associated
    game IDs. We'll merge postings together when
    merging indexes.
    """

    def __init__(self, tag: str):
        self._tag: str = tag
        self._games: list[int] = []
    
    @property
    def tag(self):
        return self._tag

    @property
    def games(self):
        return self._games
    
    def merge_postings(self, posting: Self) -> None:
        self._games.extend(posting.games)
        self._games.sort()
    
    def add_game(self, game: int) -> None:
        self._games.append(game)
    
    def sort_games(self) -> None:
        self._games.sort()
    
    def __repr__(self):
        return str(self)

    def __str__(self):
        return f"{self.tag}:{self._games}"

INDEX_NAME = "./data/index.backlog_buddy"
INDEX_NAME_TEMP = "./data/index_temp.backlog_buddy"

class Index:
    """
    Class that represents our index.
    """
    def __init__(self) -> None:
        self._path = Path(INDEX_NAME)
        self._path.touch(exist_ok=True)
        self._num_tags = 0

        self._db_final = GameDatabse()
        self._db_temp = GameDatabse(temp=True)
    
    def _get_num_tags(self) -> None:
        with self._path.open('r') as f:
            for _ in f:
                self._num_tags += 1
    
    def update_index(self):
        data_to_write: list[TagPosting] = IndexProcessor.create_in_memory_index(self._db_temp)


class IndexProcessor:
    """
    Class that modifies data for index
    """

    @staticmethod
    def write_to_final_index(index_path: Path):
        pass

    @staticmethod
    def create_in_memory_index(db_temp: GameDatabse) -> list[TagPosting]:
        
        temp_index: dict[TagPosting] = dict()

        with db_temp as database:
            games = database.get_all_games_stored()
            for game in games:
                genres = database.get_genre(game).strip(',').split(',')
                for genre in genres:
                    result = temp_index.get(genre)

                    if (result): temp_index[genre].add_game(game)
                    else: 
                        posting = TagPosting(genre)
                        posting.add_game(game)
                        temp_index[genre] = posting
        
        for games in temp_index.values():
            games.sort_games()
        
        postings = [i for i in temp_index.values()]
        postings.sort(key=lambda x: x.tag)
        
        return postings
        
    @staticmethod
    def merge_index_and_write_to_temp_index(index_path: Path):
        pass

if __name__ == "__main__":
    i = Index()
    i.update_index()