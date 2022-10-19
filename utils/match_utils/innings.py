import pandas as pd


class Innings:

    def __init__(self, base_path, tournament):
        innings_file_name = f"{base_path}/{tournament}/innings.csv"
        self.df = pd.read_csv(innings_file_name)

    def get_innings(self, match_key):
        return self.df[(self.df["match_key"] == int(match_key))]