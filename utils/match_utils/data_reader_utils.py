import pandas as pd
import datetime

# TODO: Move to an external config file
INPUT_DIRECTORY = "data/generated/match_data/cricsheet/"
TOURNAMENT_FILE_NAME = INPUT_DIRECTORY + "tournaments.csv"


class Tournaments:
    """
    Class that encapsulates all known tournament data and also stores any static config related to tournaments.
    Initialising the class reads the content from the tournament file
    """

    def __init__(self, tournament_file_name=TOURNAMENT_FILE_NAME):
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
            self.match_map[tournament] = Matches(tournament)

    def set_selected_names(self, selected_names):
        self.selected = self.df[self.df["name"].isin(selected_names)]["key"].tolist()


class Matches:
    """
        Class that encapsulates all known matches data and also stores any static config related to matches.
        Initialising the class reads the content from the matches file per tournament
    """

    def __init__(self, tournament):
        match_file_name = f"{INPUT_DIRECTORY}/{tournament}/matches.csv"
        self.df = pd.read_csv(match_file_name)
        self.df['date'] = pd.to_datetime(self.df['date']).dt.date

    def get_selected_matches(self, start_date, end_date):
        return self.df[(self.df["date"] >= start_date) & (self.df["date"] <= end_date)]

    def get_selected_match_count(self, start_date, end_date):
        selected_df = self.get_selected_matches(start_date, end_date)
        return len(selected_df.index)