import pandas as pd


class Players:
    """
    A class representing all player information as read from the metadata file
    """
    def __init__(self, player_file):
        self.players_df = pd.read_csv(player_file)

