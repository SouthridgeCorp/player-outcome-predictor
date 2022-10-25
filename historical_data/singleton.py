from historical_data.tournaments import Tournaments
from historical_data.players import Players
import streamlit as st


def get_helper(input_directory, tournament_file_name, player_file_name):
    """
    This function returns a singleton instance of the Helper (by utilising the streamlit session state).
    Note: this function only works in the streamlit context
    :param input_directory: The name of the directory where the data is stored
    :param tournament_file_name: The name of the tournaments file
    :param player_file_name: The name of the players file
    :return:
    """
    if 'MatchUtilsHelper' not in st.session_state:
        st.session_state['MatchUtilsHelper'] = Helper(input_directory, tournament_file_name, player_file_name)
    return st.session_state['MatchUtilsHelper']


class Helper:
    """
    Helper class which houses the Tournaments & Players file for future business logic implementation
    """

    def __init__(self, input_directory, tournament_file_name, player_file_name):
        self.tournaments = Tournaments(input_directory, tournament_file_name)
        player_file = f"{input_directory}/{player_file_name}"
        self.players = Players(player_file)
