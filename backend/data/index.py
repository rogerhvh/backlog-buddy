
from pathlib import Path
from data.game_database import GameDatabase
from data.index_processor import IndexProcessor
from data.tag_posting import TagPosting
from data.search_processor import SearchProcessor

TAG_VECTOR_NAME = "./data/tag_vector.backlog_buddy"
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
        self._path_tag_vector = Path(TAG_VECTOR_NAME)
        self._path_tag_vector.touch(exist_ok=True)
        self._num_tags = 0

        self._db_final = GameDatabase()
        self._db_temp = GameDatabase(temp=True)
    
    def _get_num_tags(self) -> None:
        with self._path.open('r') as f:
            for line in f:
                self._num_tags += len(line.split(':')[1].split(','))
    
    def update_index(self):
        temp_postings: list[TagPosting] = IndexProcessor.create_in_memory_index(self._db_temp)

        if (temp_postings):
            IndexProcessor.merge_index_and_write_to_temp_index(self._path, self._path_temp, temp_postings)
            IndexProcessor.write_to_final_index(self._path, self._path_temp)
            IndexProcessor.write_to_final_database(self._db_temp, self._db_final)
        
        self._path_temp.unlink()
        self._get_num_tags()

        # Then, we calculate the IDF scores
        tag_idf: dict[str, float] = SearchProcessor.get_tag_idf(self._num_tags, self._path)
        SearchProcessor.write_tag_idf(tag_idf, self._path_tag_vector)

        # Then calculate the data for each entry in the database
        # TODO: Add a new column in our database that represents the ||D|| score
        # using the values in tag_idf