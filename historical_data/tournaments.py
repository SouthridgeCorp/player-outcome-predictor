import pandas as pd

from historical_data.matches import Matches
from historical_data.playing_xi import PlayingXI
from historical_data.innings import Innings
import datetime
import logging

logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)
logger = logging.getLogger(__name__)

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

        logger.debug("Initialising tournaments")
        self.base_path = base_path
        tournament_file_name = f"{base_path}/{tournament_file}"

        # Read the dataset
        self.df = pd.read_csv(tournament_file_name)

        # Set up the data types for dates (makes it easier for date comparisons
        self.df['first_match_date'] = pd.to_datetime(self.df['first_match_date']).dt.date
        self.df['last_match_date'] = pd.to_datetime(self.df['last_match_date']).dt.date

        self.first_match_date = self.df["first_match_date"].min()
        self.last_match_date = self.df["last_match_date"].max()

        # Represents the selected training details
        self.training_selected_tournaments = []
        self.training_start = self.first_match_date
        self.training_end = self.last_match_date

        # represents the selected testing details
        self.testing_selected_tournament = ""
        self.testing_selected_tournament_name = ""
        self.testing_selected_season = ""

        logger.debug("Getting all artefacts")

        # Populate the artefacts related to the tournament
        tournaments = self.df["key"].to_list()
        self.artefacts = {}
        for tournament in tournaments:
            self.artefacts[tournament] = ArtefactsPerTournament(base_path, tournament)

        logger.debug("Getting all innings")
        self.all_innings = self.get_all_innings()

        logger.debug("Getting all matches")
        self.all_matches = self.get_all_matches()

        logger.debug("Done Initialising tournaments")

    def get_training_start_end_dates(self) -> (datetime.date, datetime.date):
        """
        Get the start / end dates set in the for training
        :return: A tuple of 2 dates
        """
        return self.training_start, self.training_end

    def set_training_window(self, start_date: datetime.date, end_date: datetime.date):
        """
        Sets the training window
        :param start_date: The start date to be set
        :param end_date: The end date to be set
        :return: None
        """
        self.training_start = start_date
        self.training_end = end_date
        self.training_selected_tournaments = self.df['key'].unique().tolist()

    def get_selected_training_tournaments(self) -> list:
        """
        Gets the list of selected tournaments for training
        :return: A list of tournament keys
        """
        return self.training_selected_tournaments

    def get_selected_training_tournament_names(self) -> list:
        """
        Gets the list of selected tournaments for training
        :return: A list of tournament names
        """
        tournaments = self.get_selected_tournaments()
        return self.df[self.df["key"].isin(tournaments)]["name"].tolist()

    def set_training_selected_tournament_names(self, selected_names: list):
        """
        Set the selected training tournament details based on the input list
        :param selected_names: The names of tournaments that have been selected
        :return: None
        """
        self.training_selected_tournaments = self.df[self.df["name"].isin(selected_names)]["key"].tolist()

    def set_testing_details(self, tournament, season):
        """
        Set the selected testing details
        :param tournament: The name of the testing tournament
        :param season: The specific season to test for
        :return: None
        """
        self.testing_selected_tournament = self.df[self.df["name"] == tournament].iloc[0]['key']
        self.testing_selected_tournament_name = tournament
        self.testing_selected_season = season

    def get_testing_details(self) -> (str, str, str):
        """
        Get the selected testing details
        :return: The selected tournament key, name and season as a tuple
        """
        return self.testing_selected_tournament, self.testing_selected_tournament_name, self.testing_selected_season

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

    def get_all_matches(self) -> pd.DataFrame:
        """
        Get all matches that we know about. Calculates the list from scratch and hence may have a performance impact.
        :return: pd.DataFrame listing all the matches information avaialble
        """
        matches_list = []

        for tournament in self.artefacts.keys():
            matches_list.append(self.artefacts[tournament].matches.get_match_df())

        return pd.concat(matches_list)

    def get_all_innings(self) -> pd.DataFrame:
        """
        Get all innings that we know about. Calculates the list from scratch and hence may have a performance impact.
        :return: pd.DataFrame listing all the innings information avaialble
        """
        innings_list = []

        for tournament in self.artefacts.keys():
            innings_list.append(self.artefacts[tournament].innings.get_data())

        return pd.concat(innings_list)

    def get_all_matches_and_innings_cached(self) -> (pd.DataFrame, pd.DataFrame):
        """
        Returns copies of the pre-cached version of all matches & innings
        """
        return self.all_matches.copy(), self.all_innings.copy()

    def get_selected_matches(self, is_testing: bool) -> pd.DataFrame:
        """
        Get all matches from selected tournaments filtered for is_testing
        :param is_testing: Set True if testing data is needed, else set False
        :return: pd.DataFrame listing all matches from selected tournaments in training/testing window
        """
        if is_testing:
            return self.matches(self.testing_selected_tournament).get_selected_matches_by_seasons(
                [self.testing_selected_season])
        else:
            start_date, end_date = self.get_training_start_end_dates()

            selected_matches_list = []
            for tournament in self.training_selected_tournaments:
                matches = self.matches(tournament).get_selected_matches(start_date, end_date)
                selected_matches_list.append(matches)
            selected_matches_df = pd.concat(selected_matches_list)
            return selected_matches_df

    def get_selected_innings(self, is_testing: bool) -> pd.DataFrame:
        """
        Get ball_by_ball pre-processed innings data from matches in selected tournaments filtered for is_testing
        :param is_testing: Set True if testing data is needed, else set False
        :return: pd.DataFrame listing all balls in all innings from matches in selected tournaments in training/testing
        window
        """
        if is_testing:
            match_keys = self.matches(self.testing_selected_tournament). \
                get_selected_match_keys_by_seasons([self.testing_selected_season])
            return self.innings(self.testing_selected_tournament).get_innings_from_match_list(match_keys)
        else:

            innings_list = []
            start_date, end_date = self.get_training_start_end_dates()

            for tournament in self.training_selected_tournaments:
                matches = self.matches(tournament)
                match_keys = matches.get_selected_match_keys(start_date, end_date)
                innings_list.append(self.innings(tournament).get_innings_from_match_list(match_keys))

            innings_df = pd.concat(innings_list)
            return innings_df

    def get_selected_teams(self, is_testing: bool) -> list:
        """
        Gets the teams for the testing or training window
        :param is_testing True for testing, false for training
        :return: A list of teams
        """
        if is_testing:
            return self.matches(self.testing_selected_tournament).get_selected_teams_by_season(
                [self.testing_selected_season])
        else:
            start_date, end_date = self.get_training_start_end_dates()
            selected_teams = []
            for tournament in self.training_selected_tournaments:
                match = self.matches(tournament)
                selected_teams += match.get_selected_teams(start_date, end_date)

            return list(set(selected_teams))

    def get_selected_playing_xi(self, is_testing: bool) -> pd.DataFrame:
        """
        Gets the playing xi for the testing or training window
        :param is_testing True for testing, false for training
        :return: A dataframe with the following columns: ["team", "match_key", "player_key"]
        """
        if is_testing:
            playing_xi_list = []
            matches = self.matches(self.testing_selected_tournament)
            match_keys = matches.get_selected_match_keys_by_seasons([self.testing_selected_season])
            for key in match_keys:
                team1, team2 = matches.get_teams(key)
                playing_xi_list.append(
                    self.playing_xi(self.testing_selected_tournament).get_playing_xi(key, team1))
                playing_xi_list.append(
                    self.playing_xi(self.testing_selected_tournament).get_playing_xi(key, team2))
        else:
            playing_xi_list = []
            start_date, end_date = self.get_training_start_end_dates()

            for tournament in self.training_selected_tournaments:
                matches = self.matches(tournament)
                match_keys = matches.get_selected_match_keys(start_date, end_date)
                for key in match_keys:
                    team1, team2 = matches.get_teams(key)
                    playing_xi_list.append(
                        self.playing_xi(tournament).get_playing_xi(key, team1))
                    playing_xi_list.append(
                        self.playing_xi(tournament).get_playing_xi(key, team2))

        if len(playing_xi_list) > 0:
            playing_xi_df = pd.concat(playing_xi_list)
        else:
            playing_xi_df = pd.DataFrame()
        return playing_xi_df

    def get_key(self, name) -> str:
        """
        Maps the tournament name to its key
        """
        return self.df[self.df["name"] == name].iloc[0]["key"]

    def get_selected_venues(self, is_testing: bool) -> list:
        """
        Get a list of venues associated with the testing or training window
        :param is_testing True for testing, false for training
        :return: A list of venues
        """
        if is_testing:
            return self.matches(self.testing_selected_tournament).\
                get_selected_venues_by_season([self.testing_selected_season])
        else:
            start_date, end_date = self.get_training_start_end_dates()
            selected_venues = []
            for tournament in self.training_selected_tournaments:
                match = self.matches(tournament)
                selected_venues += match.get_selected_venues(start_date, end_date)

            return list(set(selected_venues))

    def get_first_testing_date(self) -> datetime.date:
        """
        Get the date when the first match of the testing season was played
        """
        testing_matches = self.get_selected_matches(True)
        return testing_matches["date"].min()

    def get_tournament_and_season_details(self) -> pd.DataFrame:
        """
        Returns all the seasons associated with this object
        @return a dataframe containing:
            'tournament_key': the key of the tournament
            'season': The specific season of the tournament
            'date': The start date of the season in question
        """
        seasons_df = pd.DataFrame()
        for key in self.artefacts.keys():
            match = self.artefacts[key].matches
            seasons_df = pd.concat([seasons_df, match.get_season_with_start_date_df()])

        return seasons_df

    def get_season_details_for_window(self, start_date: datetime.date, end_date: datetime.date) -> pd.DataFrame:
        """
       Gets a list of seasons and their corresponding match counts
       @return a dataframe containing:
           'name': the name of the tournament
           'season': The specific season of the tournament
           'number_of_matches': The number of matches played for the specific tournament & season
       """
        seasons_df = pd.DataFrame()
        for key in self.artefacts.keys():
            match = self.artefacts[key].matches

            seasons_df = pd.concat([seasons_df, match.get_seasons_df_for_window(start_date, end_date)])
        seasons_df = pd.merge(seasons_df, self.df[['key', 'name']], left_on='tournament_key', right_on='key')

        return seasons_df[['name', 'season', 'number_of_matches']]
