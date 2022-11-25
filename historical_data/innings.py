import pandas as pd

import warnings
warnings.filterwarnings('ignore')

class Innings:
    """
    A class to store all innings data corresponding to a tournament
    """

    def __init__(self, base_path, tournament):
        innings_file_name = f"{base_path}/{tournament}/innings.csv"
        self.df = pd.read_csv(innings_file_name)

    def get_innings(self, match_key):
        """
        Return the innings (ball-by-ball) data corresponding to a match
        :param match_key: The match key to look for
        :return: A dataframe with ball-by-ball innings details for the match
        """
        return self.df[(self.df["match_key"] == int(match_key))]

    def get_innings_from_match_list(self, match_keys):
        """
        Return the innings (ball-by-ball) data corresponding to a match
        :param match_keys: The list of match keys to look for
        :return: A dataframe with ball-by-ball innings details for the match
        """
        return self.df[(self.df["match_key"].isin(match_keys))]

    def get_data(self) -> pd.DataFrame:
        """
        Returns a copy of the underlying innings information
        :return A copy of the innings info
        """
        return self.df.copy()
