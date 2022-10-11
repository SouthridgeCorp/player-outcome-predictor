import pandas as pd

# TODO: Move to an external config file
MATCH_FILE_NAME = "data/generated/match_data/matches.csv"
TOURNAMENT_FILE_NAME = "data/generated/match_data/tournaments.csv"


class Tournaments:
    '''
    Class that encapsulates all known tournament data and also stores any static config related to tournaments.
    Initialising the class reads the content from the tournament file
    '''
    def __init__(self, tournament_file_name=TOURNAMENT_FILE_NAME):
        self.df = pd.read_csv(tournament_file_name)
        if len(self.df['start_date']) >= 6:
            self.training_start = self.df['start_date'][0]
            self.training_end = self.df['start_date'][3]
            self.testing_start = self.df['start_date'][3]
            self.testing_end = self.df['start_date'][6]
        else:
            self.training_start = self.df['start_date'][0]
            self.training_end = self.df['start_date'][0]
            self.testing_start = self.df['start_date'][0]
            self.testing_end = self.df['start_date'][0]


class Matches:
    '''
        Class that encapsulates all known matches data and also stores any static config related to matches.
        Initialising the class reads the content from the tournament file
    '''
    def __init__(self, match_file_name = MATCH_FILE_NAME):
        self.df = pd.read_csv(match_file_name)
