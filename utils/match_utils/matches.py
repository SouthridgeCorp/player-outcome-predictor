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

    def get_selected_matches(self, start_date, end_date):
        """
        Find all matches between the specified date range
        :param start_date: The start of the date range
        :param end_date: The end of the date range
        :return: A dataframe containing all the matches which took place within the date range
        """
        return self.df[(self.df["date"] >= start_date) & (self.df["date"] <= end_date)]

    def get_selected_match_count(self, start_date, end_date):
        """
        Gets the number of matches that have been selected within the specified date range
        :param start_date: The start of the date range
        :param end_date: The end of the date range
        :return: The number of matches which took place within the date range
        """
        selected_df = self.get_selected_matches(start_date, end_date)
        return len(selected_df.index)