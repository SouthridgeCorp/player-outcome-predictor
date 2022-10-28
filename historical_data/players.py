import pandas as pd


class Players:
    """
    A class representing all player information as read from the metadata file
    """
    def __init__(self, player_file):
        self.players_df = pd.read_csv(player_file)
        self.players_df.set_index("key")

    def merge_with_players(self, source_df: pd.DataFrame, source_key: str) -> pd.DataFrame:
        """
        Merges the player details with the source column to create a combined dataframe
        :param source_df: The dataframe to merge with
        :param source_key: The key for the source df
        :return: The merged df
        """
        df = pd.merge(self.players_df, source_df, left_on="key", right_on=source_key)
        df.drop('key', axis=1, inplace=True)
        return df
