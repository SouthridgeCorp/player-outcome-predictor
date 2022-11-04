from historical_data.tournaments import Tournaments
from historical_data.players import Players
from utils.config_utils import ConfigUtils


class Helper:
    """
    Helper class which houses the Tournaments & Players file for future business logic implementation
    """

    def __init__(self, config_utils: ConfigUtils):
        input_directory = config_utils.get_input_directory()
        tournament_file_name = config_utils.get_tournament_file_name()
        player_file_name = config_utils.get_player_file_name()
        self.tournaments = Tournaments(input_directory, tournament_file_name)
        player_file = f"{input_directory}/{player_file_name}"
        self.players = Players(player_file)


