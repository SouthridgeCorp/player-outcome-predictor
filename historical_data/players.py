import pandas as pd


class Players:
    """
    A class representing all player information as read from the metadata file
    """
    def __init__(self, player_file):
        self.players_df = pd.read_csv(player_file)
        self.players_df.set_index("key")

    def get_players(self) -> pd.DataFrame:
        """
        Returns a copy of all the players that we know about
        :return: pd.DataFrame listing all the player information available
        """
        return self.players_df.copy()

    def merge_with_players(self, source_df: pd.DataFrame, source_key: str, source_left=False) -> pd.DataFrame:
        """
        Merges the player details with the source column to create a combined dataframe
        :param source_df: The dataframe to merge with
        :param source_key: The key for the source df
        :param source_left: The direction in which the source df should be merged
        :return: The merged df
        """
        if source_left:
            df = pd.merge(source_df, self.players_df, right_on="key", left_on=source_key)
        else:
            df = pd.merge(self.players_df, source_df, left_on="key", right_on=source_key)
        df.drop('key', axis=1, inplace=True)
        return df

