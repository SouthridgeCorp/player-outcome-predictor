import pandas as pd


class Players:
    def __init__(self, player_file):
        self.players_df = pd.read_csv(player_file)
