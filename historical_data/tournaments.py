import pandas as pd

from historical_data.matches import Matches
from historical_data.playing_xi import PlayingXI
from historical_data.innings import Innings
import datetime


class ArtefactsPerTournament:
    """
    A collection of all artefacts organised under a tournament
    """

    def __init__(self, base_path, tournament):
        self.matches = Matches(base_path, tournament)
        self.playing_xi = PlayingXI(base_path, tournament)
        self.innings = Innings(base_path, tournament)


class Tournaments:
    """
    Class that encapsulates all known tournament data and also stores any static config related to tournaments.
    Initialising the class reads the content from the tournament file
    """

    def __init__(self, base_path, tournament_file):
        self.base_path = base_path
        tournament_file_name = f"{base_path}/{tournament_file}"

        # Read the dataset
        self.df = pd.read_csv(tournament_file_name)

        # Set up the data types for dates (makes it easier for date comparisons
        self.df['first_match_date'] = pd.to_datetime(self.df['first_match_date']).dt.date
        self.df['last_match_date'] = pd.to_datetime(self.df['last_match_date']).dt.date

        self.first_match_date = self.df["first_match_date"].min()
        self.last_match_date = self.df["last_match_date"].max()

        # Set default limits for training & testing date ranges
        self.training_start = self.first_match_date
        self.training_end = self.last_match_date
        self.testing_start = self.first_match_date
        self.testing_end = self.last_match_date

        # represents the selected set of tournaments, based on user selection
        self.selected = []

        # Populate the artefacts related to the tournament
        tournaments = self.df["key"].to_list()
        self.artefacts = {}
        for tournament in tournaments:
            self.artefacts[tournament] = ArtefactsPerTournament(base_path, tournament)

    def get_start_end_dates(self, is_testing) -> (datetime.date, datetime.date):
        if is_testing:
            return self.testing_start, self.testing_end
        else:
            return self.training_start, self.training_end

    def set_testing_dates(self, start_date: datetime.date, end_date: datetime.date):
        self.testing_start = start_date
        self.testing_end = end_date

    def set_training_dates(self, start_date: datetime.date, end_date: datetime.date):
        self.training_start = start_date
        self.training_end = end_date

    def get_selected_tournaments(self):
        return self.selected

    def set_selected_tournament_names(self, selected_names: list):
        """
        Set the selected tournament details based on user selection
        :param selected_names: The names of tournaments that have been selected
        :return: None
        """
        self.selected = self.df[self.df["name"].isin(selected_names)]["key"].tolist()


    def matches(self, tournament):
        """
        Get the matches corresponding to a tournament. If a tournament does not exist, this function will throw an error
        :param tournament: The tournament to look for
        :return: The Matches object mapped to the tournament
        """
        return self.artefacts[tournament].matches

    def innings(self, tournament):
        """
        Get the Innings corresponding to a tournament. If a tournament does not exist, this function will throw an error
        :param tournament: The tournament to look for
        :return: The Innings object mapped to the tournament
        """
        return self.artefacts[tournament].innings

    def playing_xi(self, tournament):
        """
        Get the playing xi corresponding to a tournament. If a tournament does not exist, this function will throw an error
        :param tournament: The tournament to look for
        :return: The PlayingXI object mapped to the tournament
        """
        return self.artefacts[tournament].playing_xi
