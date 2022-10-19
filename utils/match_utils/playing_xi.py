import pandas as pd


class PlayingXI:

    def __init__(self, base_path, tournament):
        playing_xi_file_name = f"{base_path}/{tournament}/playing_xi.csv"
        self.df = pd.read_csv(playing_xi_file_name)

    def get_playing_xi(self, match_key, team):
        return self.df[(self.df["match_key"] == int(match_key)) & (self.df["team"] == team)]