from utils.match_utils.tournaments import Tournaments
from utils.match_utils.players import Players

# TODO: Move to an external config file
INPUT_DIRECTORY = "data/generated/match_data/cricsheet/"
TOURNAMENT_FILE_NAME = "tournaments.csv"
PLAYER_FILE_NAME = "players.csv"


class Helper:
    def __init__(self, input_directory=INPUT_DIRECTORY,
                 tournament_file_name=TOURNAMENT_FILE_NAME, player_file_name=PLAYER_FILE_NAME):

        self.tournaments = Tournaments(input_directory, tournament_file_name)
        player_file = f"{input_directory}/{player_file_name}"
        self.players = Players(player_file)
