
from pathlib import Path
from data.game_database import GameDatabse
from data.index_processor import IndexProcessor
from data.tag_posting import TagPosting

INDEX_NAME = "./data/index.backlog_buddy"
INDEX_NAME_TEMP = "./data/index_temp.backlog_buddy"

class Index:
    """
    Class that represents our index.
    """
    def __init__(self) -> None:
        self._path = Path(INDEX_NAME)
        self._path.touch(exist_ok=True)
        self._path_temp = Path(INDEX_NAME_TEMP)
        self._path_temp.touch()
        self._num_tags = 0

        self._db_final = GameDatabse()
        self._db_temp = GameDatabse(temp=True)
    
    def _get_num_tags(self) -> None:
        with self._path.open('r') as f:
            for _ in f:
                self._num_tags += 1
    
    def update_index(self):
        temp_postings: list[TagPosting] = IndexProcessor.create_in_memory_index(self._db_temp)

        if (temp_postings):
            IndexProcessor.merge_index_and_write_to_temp_index(self._path, self._path_temp, temp_postings)
            IndexProcessor.write_to_final_index(self._path, self._path_temp)
            IndexProcessor.write_to_final_database(self._db_temp, self._db_final)
        
        self._get_num_tags()
        # Then, we calculate the document vector

