
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
    
    @staticmethod
    def str_to_tag(line: str) -> Self:
        """
        Converts string to a TagPosting object.
        """
        line = line.split(':')
        tag = line[0]
        games = line[1].split(',')

        # No need to sort here because we sort when writing.
        p = TagPosting(tag)
        for game in games:
            p.add_game(int(game))
        return p
    
    def __repr__(self):
        return str(self)

    def __str__(self):
        return f"{self.tag}:{','.join([str(i) for i in self._games])}"