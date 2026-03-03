
from pathlib import Path
from data.game_database import GameDatabase
from data.index_processor import IndexProcessor
from data.tag_posting import TagPosting
from data.search_processor import SearchProcessor

TAG_IDF_NAME = "./data/tag_idf.backlog_buddy"
INDEX_NAME = "./data/index.backlog_buddy"
INDEX_NAME_TEMP = "./data/index_temp.backlog_buddy"

"""
NOTE:

INDEX FORMAT IS AS-FOLLOWS:
    TAG:GAME_ID1,GAME_ID2, ... ,GAME_IDN
    TAG2:...
    ...
    TAGN

    If you have any questions ask Aedan!
"""

class Index:
    """
    Class that represents our index.
    """
    def __init__(self) -> None:
        self._path = Path(INDEX_NAME)
        self._path.touch(exist_ok=True)
        self._path_temp = Path(INDEX_NAME_TEMP)
        self._path_temp.touch()
        self._path_tag_vector = Path(TAG_IDF_NAME)
        self._path_tag_vector.touch(exist_ok=True)
        self._num_tags = 0

        self._db_final = GameDatabase()
        self._db_temp = GameDatabase(temp=True)

        self._tag_idfs = None
    
    def update_index(self) -> None:
        """
        Public function that handles index update and rebuild logic.
        """
        temp_postings: list[TagPosting] = IndexProcessor.create_in_memory_index(self._db_temp)

        if (temp_postings):
            IndexProcessor.merge_index_and_write_to_temp_index(self._path, self._path_temp, temp_postings)
            IndexProcessor.write_to_final_index(self._path, self._path_temp)
            IndexProcessor.write_to_final_database(self._db_temp, self._db_final)
            self._num_tags = IndexProcessor.get_num_games(self._db_final)

            # Then, we calculate the new IDF scores
            self._tag_idfs: dict[str, float] = SearchProcessor.get_tag_idf(self._num_tags, self._path)
            SearchProcessor.write_tag_idf(self._tag_idfs, self._path_tag_vector)

            # Then calculate the data for each entry in the database
            SearchProcessor.update_l2_norm(self._tag_idfs, self._db_final)

        self._path_temp.unlink()
