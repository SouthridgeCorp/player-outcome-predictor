import pandas as pd

from utils.match_utils.matches import Matches


class Tournaments:
    """
    Class that encapsulates all known tournament data and also stores any static config related to tournaments.
    Initialising the class reads the content from the tournament file
    """

    def __init__(self, base_path, tournament_file):
        self.base_path = base_path
        tournament_file_name = f"{base_path}/{tournament_file}"
        # Initialise the function
        self.df = pd.read_csv(tournament_file_name)

        self.df['first_match_date'] = pd.to_datetime(self.df['first_match_date']).dt.date
        self.df['last_match_date'] = pd.to_datetime(self.df['last_match_date']).dt.date

        first_match_date = self.df["first_match_date"].min()
        last_match_date = self.df["last_match_date"].max()

        self.training_start = first_match_date
        self.training_end = last_match_date
        self.testing_start = first_match_date
        self.testing_end = last_match_date

        self.selected = []
        self.match_map = {}

        tournaments = self.df["key"].to_list()

        for tournament in tournaments:
            self.match_map[tournament] = Matches(base_path, tournament)

    def set_selected_names(self, selected_names):
        self.selected = self.df[self.df["name"].isin(selected_names)]["key"].tolist()