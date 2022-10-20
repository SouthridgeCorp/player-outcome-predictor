import pandas as pd


class PlayingXI:
    """
    Class representing the PlayingXI related to a tournament
    """

    def __init__(self, base_path, tournament):
        playing_xi_file_name = f"{base_path}/{tournament}/playing_xi.csv"
        self.df = pd.read_csv(playing_xi_file_name)

    def get_playing_xi(self, match_key, team):
        """
        Find the playing XI for a specific match & team
        :param match_key: The match to look for
        :param team: the team to look for
        :return: A dataframe representing the playing XI for the match & team specified
        """
        return self.df[(self.df["match_key"] == int(match_key)) & (self.df["team"] == team)]