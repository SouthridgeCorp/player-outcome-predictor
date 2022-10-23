from historical_data.tournaments import Tournaments
from historical_data.players import Players
import streamlit as st

# TODO: Move to an external config file
TOURNAMENT_FILE_NAME = "tournaments.csv"
PLAYER_FILE_NAME = "players.csv"


def get_helper(input_directory, tournament_file_name, player_file_name):
    if 'MatchUtilsHelper' not in st.session_state:
        st.session_state['MatchUtilsHelper'] = Helper(input_directory, tournament_file_name, player_file_name)
    return st.session_state['MatchUtilsHelper']


class Helper:
    def __init__(self, input_directory, tournament_file_name, player_file_name):
        self.tournaments = Tournaments(input_directory, tournament_file_name)
        player_file = f"{input_directory}/{player_file_name}"
        self.players = Players(player_file)
