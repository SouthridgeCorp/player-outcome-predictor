import pandas as pd

MATCH_FILE_NAME = "resources/match_data/matches.csv"
TOURNAMENT_FILE_NAME = "resources/match_data/tournaments.csv"


class Tournaments:
    '''
    Class that encapsulates all known tournament data and also stores any static config related to tournaments.
    Initialising the class reads the content from the tournament file
    '''
    def __init__(self, tournament_file_name=TOURNAMENT_FILE_NAME):
        self.df = pd.read_csv(tournament_file_name)
        self.training_start = self.df['start_date'][1]
        self.training_end = self.df['start_date'][3]
        self.testing_start = self.df['start_date'][3]
        self.testing_end = self.df['start_date'][6]


class Matches:
    '''
        Class that encapsulates all known matches data and also stores any static config related to matches.
        Initialising the class reads the content from the tournament file
    '''
    def __init__(self, match_file_name = MATCH_FILE_NAME):
        self.match_df = pd.read_csv(match_file_name)
