import datetime

import pandas as pd


class Matches:
    """
    Class that encapsulates all known matches data and also stores any static config related to matches.
    Initialising the class reads the content from the matches file per tournament
    """

    def __init__(self, base_path, tournament):
        match_file_name = f"{base_path}/{tournament}/matches.csv"
        self.df = pd.read_csv(match_file_name)
        self.df['date'] = pd.to_datetime(self.df['date']).dt.date

    def get_number_of_matches(self):
        """
        Return number of matches inside this object
        :return:
        """
        return len(self.df["key"])

    def get_selected_matches(self, start_date: datetime.date, end_date: datetime.date):
        """
        Find all matches between the specified date range
        :param start_date: The start of the date range
        :param end_date: The end of the date range
        :return: A dataframe containing all the matches which took place within the date range
        """
        return self.df[(self.df["date"] >= start_date) & (self.df["date"] <= end_date)]

    def get_selected_matches_by_seasons(self, list_of_seasons) -> pd.DataFrame:
        """
        Find all matches for the specified set of seasons
        :param list_of_seasons: The list of seasons to look for
        :return: A dataframe containing all the matches which took place for the specified seasons
      """

        return self.df[self.df["season"].isin(list_of_seasons)]

    def get_selected_match_count(self, start_date, end_date):
        """
        Gets the number of matches that have been selected within the specified date range
        :param start_date: The start of the date range
        :param end_date: The end of the date range
        :return: The number of matches which took place within the date range
        """
        selected_df = self.get_selected_matches(start_date, end_date)
        return len(selected_df.index)

    def get_selected_match_count_by_seasons(self, list_of_seasons):
        """
        Gets the number of matches that have been selected for the specified seasons
        :param list_of_seasons: The list of seasons to look for
        :return: The number of matches which took place for the selected seasons
        """
        selected_df = self.get_selected_matches_by_seasons(list_of_seasons)
        return len(selected_df.index)

    def get_selected_match_keys(self, start_date: datetime.date, end_date: datetime.date) -> list:
        """
        Get a list of match keys corresponding to the start & end date windows
        :param start_date: The starting date of the window
        :param end_date: The ending state of the window
        :return: A list of keys
        """
        selected_df = self.get_selected_matches(start_date, end_date)
        return selected_df["key"].tolist()

    def get_selected_match_keys_by_seasons(self, list_of_seasons) -> list:
        """
        Get a list of match keys corresponding to the list of seasons
        :param list_of_seasons: The list of seasons to look for
        :return: A list of keys
        """
        selected_df = self.get_selected_matches_by_seasons(list_of_seasons)
        return selected_df["key"].tolist()

    def get_teams(self, match_key: str) -> (str, str):
        """
        Get the teams playing in a match
        :param match_key: The identifier for the match in question
        :return: A tuple containing team 1 & team 2
        """
        match_df = self.df[self.df["key"] == int(match_key)]
        assert len(match_df.index) == 1
        team1 = match_df.iloc[0]["team1"]
        team2 = match_df.iloc[0]["team2"]
        return team1, team2

    def get_selected_teams(self, start_date: datetime.date, end_date: datetime.date) -> list:
        """
        Get a list of teams corresponding to the start & end date windows
        :param start_date: The starting date of the window
        :param end_date: The ending state of the window
        :return: A list of keys
        """
        selected_df = self.get_selected_matches(start_date, end_date)
        team_list = list(selected_df["team1"])
        team_list += list(selected_df["team2"])
        return list(set(team_list))

    def get_selected_teams_by_season(self, list_of_seasons) -> list:
        """
        Get a list of teams corresponding to the seasons in question
        :param list_of_seasons: List of seasons for which the venue list must be queried
        :return: A list of teams
        """
        selected_df = self.get_selected_matches_by_seasons(list_of_seasons)
        team_list = list(selected_df["team1"])
        team_list += list(selected_df["team2"])
        return list(set(team_list))

    def get_selected_venues(self, start_date: datetime.date, end_date: datetime.date) -> list:
        """
        Get a list of venues corresponding to the start & end date windows
        :param start_date: The starting date of the window
        :param end_date: The ending state of the window
        :return: A list of venues
        """
        selected_df = self.get_selected_matches(start_date, end_date)
        return list(set(list(selected_df["venue"])))

    def get_selected_venues_by_season(self, list_of_seasons) -> list:
        """
        Get a list of venues corresponding to the list of seasons provided
        :param list_of_seasons: List of seasons for which the venue list must be queried
        :return: A list of venues
        """
        selected_df = self.get_selected_matches_by_seasons(list_of_seasons)
        return list(set(list(selected_df["venue"])))

    def get_match_df(self) -> pd.DataFrame:
        """
        Returns a copy of the underlying matches dataframe
        """
        return self.df.copy()

    def get_all_seasons(self) -> list:
        """
        Returns a list of all seasons for this match set
        """
        return self.df['season'].unique().tolist()

    def get_season_with_start_date_df(self) -> pd.DataFrame:
        """
        Get a dataframe listing out all the seasons and the dates when they started
        @return a dataframe containing:
            'tournament_key': the key of the tournament
            'season': The specific season of the tournament
            'date': The start date of the season in question
        """
        seasons_df = self.df.copy().groupby('season').min().reset_index()
        return seasons_df[['tournament_key', 'season', 'date']].sort_values(by=['date'], ascending=False)

    def get_seasons_df_for_window(self, start_date: datetime.date, end_date: datetime.date) -> pd.DataFrame:
        """
        Gets a list of seasons and their corresponding match counts
        @return a dataframe containing:
            'tournament_key': the key of the tournament
            'season': The specific season of the tournament
            'number_of_matches': The number of matches played for the specific tournament & season
        """
        seasons_df = self.df[(self.df['date'] >= start_date) & (self.df['date'] < end_date)]
        seasons_df = seasons_df.copy().groupby(['tournament_key', 'season'])['key'].count().reset_index()
        seasons_df = seasons_df[['tournament_key', 'season', 'key']]
        seasons_df.rename(columns={"key": "number_of_matches"}, inplace=True)
        return seasons_df
