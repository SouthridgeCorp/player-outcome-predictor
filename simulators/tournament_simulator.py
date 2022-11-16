from utils.config_utils import ConfigUtils
from data_selection.data_selection import DataSelection
from rewards_configuration.rewards_configuration import RewardsConfiguration
import pandas as pd
import logging


class TournamentSimulator:

    def validate_source_files(self):
        matches_df = self.data_selection.get_all_matches()
        players_df = self.data_selection.get_all_players()

        # validate that the venues in the source matches is available in the overall dataset
        received_venues = set(self.source_matches_df['venue'].unique().tolist())
        expected_venues = set(matches_df['venue'].unique().tolist())

        if not received_venues.issubset(expected_venues):
            raise ValueError(f"Couldn't find some venues in the historical data.\n"
                             f"Received: {received_venues}\n"
                             f"Training venues: {expected_venues}")

        # validate that the teams in the source matches is available in the overall dataset
        received_teams = set(self.source_matches_df['team1'].unique().tolist()
                              + self.source_matches_df['team2'].unique().tolist())
        expected_teams = set(matches_df['team1'].unique().tolist() + matches_df['team2'].unique().tolist())

        if not received_teams.issubset(expected_teams):
            raise ValueError(f"Couldn't find some teams in the historical data.\n"
                             f"Received: {received_teams}\n"
                             f"Training venues: {expected_teams}")

        # validate that the players in the source matches is available in the overall dataset
        received_players = set(self.source_playing_xi_df['player_key'].unique().tolist())
        expected_players = set(players_df['key'].unique().tolist())

        if not received_players.issubset(expected_players):
            raise ValueError(f"Couldn't find some teams in the historical data.\n"
                             f"Received: {received_players}\n"
                             f"Training venues: {expected_players}")

    def __init__(self, data_selection: DataSelection, rewards_configuration: RewardsConfiguration,
                 config_utils: ConfigUtils):
        self.number_of_scenarios, matches_file_name, playing_xi_file_name = config_utils.get_tournament_simulator_info()
        self.data_selection = data_selection
        self.rewards_configuration = rewards_configuration

        self.source_matches_df = pd.read_csv(matches_file_name)
        self.source_playing_xi_df = pd.read_csv(playing_xi_file_name)
