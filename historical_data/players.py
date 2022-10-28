import pandas as pd


class Players:
    """
    A class representing all player information as read from the metadata file
    """
    def __init__(self, player_file):
        self.players_df = pd.read_csv(player_file)
        self.players_df.set_index("key")

    def merge_with_players(self, source_df, source_key) -> pd.DataFrame:
        df = pd.merge(self.players_df, source_df, left_on="key", right_on=source_key)
        df.drop('key', axis=1, inplace=True)
        return df
