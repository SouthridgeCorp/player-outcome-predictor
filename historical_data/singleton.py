from historical_data.tournaments import Tournaments
from historical_data.players import Players
import streamlit as st
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


def get_helper(config_utils: ConfigUtils) -> Helper:
    """
    This function returns a singleton instance of the Helper (by utilising the streamlit session state).
    Note: this function only works in the streamlit context
    :param config_utils: The config_utils object used to configure the helper
    :return: A Helper class
    """
    if 'MatchUtilsHelper' not in st.session_state:
        st.session_state['MatchUtilsHelper'] = Helper(config_utils)
    return st.session_state['MatchUtilsHelper']
