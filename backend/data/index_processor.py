
from data.game_database import GameDatabase
from data.tag_posting import TagPosting
from pathlib import Path

class IndexProcessor:
    """
    Class that modifies data for index
    """

    @staticmethod
    def write_to_final_index(index_path: Path, index_path_temp: Path) -> None:
        """
        Writes from temporary file to final index. 
        """

        with index_path.open('w') as f:
            with index_path_temp.open('r') as f2:
                for line in f2:
                    f.write(line)

    @staticmethod
    def create_in_memory_index(db_temp: GameDatabase) -> list[TagPosting]:
        """
        Create in-memory index for all new games added that have not been indexed.
        """
        
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
        
        postings: list[TagPosting] = [i for i in temp_index.values()]
        postings.sort(key=lambda x: x.tag)
        
        return postings
        
    @staticmethod
    def merge_index_and_write_to_temp_index(index_path: Path, 
                                            index_path_temp: Path, 
                                            temp_postings: list[TagPosting]
                                            ) -> None:
        """
        Merge in-memory index and on-disk index, then write to disk.
        """

        write_string = ""
        
        temp_postings_index = 0
        with index_path.open('r') as f:

            for line in f:
                posting: TagPosting = TagPosting.str_to_tag(line.strip())
                
                # Say, we read "Co-op" but we have "Action" in memory
                while (temp_postings_index < len(temp_postings) 
                       and posting.tag > temp_postings[temp_postings_index].tag):
                    write_string += str(temp_postings[temp_postings_index]) + '\n'
                    temp_postings_index += 1

                # Once we get here, then it means that the posting tag from disk
                # is less or equal to the temp postings.
                if (temp_postings_index < len(temp_postings)
                        and posting.tag == temp_postings[temp_postings_index].tag):
                    # Merge
                    posting.merge_postings(temp_postings[temp_postings_index])
                    temp_postings_index += 1

                # Append result, either merged or not.
                write_string += str(posting) + '\n'

        for i in range(temp_postings_index, len(temp_postings)):
            write_string += str(temp_postings[i]) + '\n'
        
        # TODO: Maybe write mid-way to ensure memory usage is not too high.
        with index_path_temp.open('w') as f:
            f.write(write_string)
    
    @staticmethod
    def write_to_final_database(db_temp: GameDatabase, db_final: GameDatabase):
        """
        Writes all updated game data to the database
        """
        with db_temp as temp_database, db_final as final_database:
            # data_to_add = temp_database.get_all_data()

            # Add data to main database
            for data in temp_database.get_all_data():
                final_database.insert(data)

            # Clears tables
            temp_database.drop_database()
            temp_database.create_database()

    @staticmethod
    def get_num_games(db_final: GameDatabase) -> int:
        """
        Helper function to get number of games.
        """
        with db_final:
            result = db_final.get_num_rows()
        return result