from utils.config_utils import ConfigUtils
from data_selection.data_selection import DataSelection
from rewards_configuration.rewards_configuration import RewardsConfiguration
import pandas as pd
import logging
from simulators.predictive_simulator import PredictiveSimulator
from datetime import datetime


class TournamentSimulator:
    """
    Simulates a tournament and calculates player rewards based on how the tournament plays out. See
    README_tournament_simulator.md.
    """

    def validate_and_setup(self):
        """
        Validates the configuration files & also setup all the data for simulations
        """
        # Ensure the number of scenarios is within the limit
        if self.number_of_scenarios >= self.max_number_of_scenarios:
            raise ValueError(f"The number of scenarios must be lesser than {self.max_number_of_scenarios}\n"
                             f"Received: {self.number_of_scenarios}")
        number_of_matches = len(self.source_matches_df.index)

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
        received_teams = set(self.source_matches_df['team1'].dropna().unique().tolist()
                             + self.source_matches_df['team2'].dropna().unique().tolist())
        expected_teams = set(matches_df['team1'].unique().tolist() + matches_df['team2'].unique().tolist())

        if not received_teams.issubset(expected_teams):
            logging.debug(f"Couldn't find some teams in the historical data.\n"
                          f"Received: {received_teams}\n"
                          f"Expected: {expected_teams}")

        # Set the match key to a sequential number > total number of historical matches
        match_key_start = matches_df['key'].max() + 1
        match_key_end = match_key_start + number_of_matches
        self.source_matches_df['key'] = range(match_key_start, match_key_end)

        # Map players to match key
        self.source_playing_xi_df = self.build_playing_xi(self.source_matches_df)

        # validate that the players in the source matches is available in the overall dataset
        received_players = set(self.source_playing_xi_df['player_key'].unique().tolist())
        expected_players = set(players_df['key'].unique().tolist())

        if not received_players.issubset(expected_players):
            raise ValueError(f"Couldn't find some players in the historical data.\n"
                             f"Received: {received_players}\n"
                             f"Expected: {expected_players}")

    def build_playing_xi(self, source_matches_df):
        """
        Map each match to its corresponding playing XI for each team
        """
        team1_df = pd.merge(source_matches_df[['key', 'team1']],
                            self.master_playing_xi_df, left_on='team1', right_on='team', how='right')
        team2_df = pd.merge(source_matches_df[['key', 'team2']],
                            self.master_playing_xi_df, left_on='team2', right_on='team', how='right')
        team1_df.drop('team1', axis=1, inplace=True)
        team2_df.drop('team2', axis=1, inplace=True)
        source_playing_xi_df = pd.concat([team1_df, team2_df])
        source_playing_xi_df.rename(columns={'key': 'match_key'}, inplace=True)
        source_playing_xi_df['match_key'] = source_playing_xi_df['match_key'].fillna(0).astype(int)

        return source_playing_xi_df

    def __init__(self, data_selection: DataSelection, rewards_configuration: RewardsConfiguration,
                 config_utils: ConfigUtils):
        self.number_of_scenarios, self.matches_file_name, self.playing_xi_file_name = \
            config_utils.get_tournament_simulator_info()
        self.data_selection = data_selection
        self.rewards_configuration = rewards_configuration

        self.source_matches_df = pd.read_csv(self.matches_file_name)
        self.source_matches_df['stage'] = self.source_matches_df['stage'].fillna('')

        self.master_playing_xi_df = pd.read_csv(self.playing_xi_file_name)
        self.source_playing_xi_df = pd.DataFrame()

        self.q1_group_stage = ['Qualifier 1']
        self.eliminator_group_stage = ['Eliminator']
        self.q2_group_stage = ['Qualifier 2']
        self.final_stage = ['Final']
        self.non_group_stages = self.final_stage + self.q1_group_stage \
                                + self.eliminator_group_stage + self.q2_group_stage

        self.group_matches_predictive_simulator = None
        self.first_non_group_matches_predictive_simulator = None
        self.second_non_group_matches_predictive_simulator = None
        self.finals_predictive_simulator = None

        self.scenario_date_time = None

        self.max_number_of_scenarios = 100

    def get_group_stage_matches(self):
        mask_for_stage = self.source_matches_df['stage'].isin(self.non_group_stages)
        return self.source_matches_df[~mask_for_stage]

    def get_first_non_group_matches(self):
        mask_for_stage = self.source_matches_df['stage'].isin(self.q1_group_stage + self.eliminator_group_stage)
        return self.source_matches_df[mask_for_stage]

    def get_second_non_group_matches(self):
        mask_for_stage = self.source_matches_df['stage'].isin(self.q2_group_stage)
        return self.source_matches_df[mask_for_stage]

    def get_final_matches(self):
        mask_for_stage = self.source_matches_df['stage'].isin(self.final_stage)
        return self.source_matches_df[mask_for_stage]

    def prepare_group_matches_and_players(self):
        """
        Prepare data for group level matches
        """
        group_stage_matches_df = self.get_group_stage_matches()
        matches_df = pd.DataFrame()
        playing_xi_df = pd.DataFrame()
        # For each scenario..
        for scenario in range(0, self.number_of_scenarios):
            matches_to_add_df = group_stage_matches_df.copy()

            # Include scenario number
            matches_to_add_df['tournament_scenario'] = scenario

            # Make sure the match key is unique per scenario so that the predictive simulator is able to treat each
            # match uniquely
            matches_to_add_df['key'] = (matches_to_add_df['key'] * self.max_number_of_scenarios) + scenario
            matches_df = pd.concat([matches_df, matches_to_add_df])

            # Build the playing xi for the match
            players_to_add_df = self.source_playing_xi_df.copy()

            # Make sure the match key is unique per scenario so that the predictive simulator is able to treat each
            # match uniquely
            players_to_add_df['match_key'] = (players_to_add_df['match_key'] * self.max_number_of_scenarios) + scenario
            playing_xi_df = pd.concat((playing_xi_df, players_to_add_df))

        return matches_df, playing_xi_df

    def prepare_non_group_matches(self, previous_winners_df, non_group_matches, stages):
        """
        Prepares the data for non group matches
        """
        matches_df = pd.DataFrame()
        playing_xi_df = pd.DataFrame()
        for scenario in range(0, self.number_of_scenarios):
            matches_to_add_df = non_group_matches.copy()
            matches_to_add_df['tournament_scenario'] = scenario

            # Set the following teams:
            #       Qualifier 1: Top 2 teams
            #       Qualifier 2: team #3 & 4
            sorted_winners_df = previous_winners_df.sort_values(by=[scenario], ascending=False)[scenario]
            team_position = 0
            for stage in stages:
                mask = self.source_matches_df['stage'] == stage
                matches_to_add_df.loc[mask, 'team1'] = sorted_winners_df.index[team_position]
                team_position += 1
                matches_to_add_df.loc[mask, 'team2'] = sorted_winners_df.index[team_position]
                team_position += 1

            # Make sure the match key is unique per scenario so that the predictive simulator is able to treat each
            # match uniquely
            matches_to_add_df['key'] = (matches_to_add_df['key'] * self.max_number_of_scenarios) + scenario
            matches_df = pd.concat([matches_df, matches_to_add_df])

            # Build the playing xi for the match
            players_to_add_df = self.build_playing_xi(matches_to_add_df)
            playing_xi_df = pd.concat((playing_xi_df, players_to_add_df))

        return matches_df, playing_xi_df

    def prepare_q1_and_eliminator_matches_and_players(self, previous_winners_df):
        """
        Prepare the data for Qualifier 1 & their corresponding playing XI
        """
        non_group_matches = self.get_first_non_group_matches()
        return self.prepare_non_group_matches(previous_winners_df,
                                              non_group_matches,
                                              self.q1_group_stage + self.eliminator_group_stage)

    def prepare_q2_matches_and_players(self, q1_and_elim_df):
        """
        Prepare the data for Qualifier 2 & their corresponding playing XI
        """
        non_group_matches = self.get_second_non_group_matches()
        previous_matches_df = q1_and_elim_df.copy()

        matches_df = pd.DataFrame()
        playing_xi_df = pd.DataFrame()
        for scenario in range(0, self.number_of_scenarios):
            matches_to_add_df = non_group_matches.copy()
            matches_to_add_df['tournament_scenario'] = scenario

            # Team 1 for Qualifier 2 = loser of Qualifier 1
            mask = (previous_matches_df['stage'] == self.q1_group_stage[0]) & \
                   (previous_matches_df['tournament_scenario'] == scenario)
            matches_to_add_df['team1'] = previous_matches_df[mask]['loser'].values[0]

            # Team 2 for Qualifier 2 = winner of Eliminator 1
            mask = (previous_matches_df['stage'] == self.eliminator_group_stage[0]) & \
                   (previous_matches_df['tournament_scenario'] == scenario)
            matches_to_add_df['team2'] = previous_matches_df[mask]['winner'].values[0]

            # Make sure the match key is unique per scenario so that the predictive simulator is able to treat each
            # match uniquely
            matches_to_add_df['key'] = (matches_to_add_df['key'] * self.max_number_of_scenarios) + scenario
            matches_df = pd.concat([matches_df, matches_to_add_df])

            # Build the playing xi for the match
            players_to_add_df = self.build_playing_xi(matches_to_add_df)
            playing_xi_df = pd.concat((playing_xi_df, players_to_add_df))

        return matches_df, playing_xi_df

    def prepare_finals_matches_and_players(self, q1_and_elim_df, q2_df):
        """
        Prepare the data for finals & their corresponding playing XI
        """
        non_group_matches = self.get_final_matches()
        matches_df = pd.DataFrame()
        playing_xi_df = pd.DataFrame()

        for scenario in range(0, self.number_of_scenarios):
            matches_to_add_df = non_group_matches.copy()
            matches_to_add_df['tournament_scenario'] = scenario

            # Team 1 for the finals = winner of Qualifier 1
            mask = (q1_and_elim_df['stage'] == self.q1_group_stage[0]) & \
                   (q1_and_elim_df['tournament_scenario'] == scenario)
            matches_to_add_df['team1'] = q1_and_elim_df[mask]['winner'].values[0]

            # Team 2 for the finals = winner of Qualifier 2
            mask = q2_df['tournament_scenario'] == scenario
            matches_to_add_df['team2'] = q2_df[mask]['winner'].values[0]

            # Make sure the match key is unique per scenario so that the predictive simulator is able to treat each
            # match uniquely
            matches_to_add_df['key'] = (matches_to_add_df['key'] * self.max_number_of_scenarios) + scenario
            matches_df = pd.concat([matches_df, matches_to_add_df])

            # Build the playing xi for the match
            players_to_add_df = self.build_playing_xi(matches_to_add_df)
            playing_xi_df = pd.concat((playing_xi_df, players_to_add_df))

        return matches_df, playing_xi_df

    def get_match_results(self, input_matches_df, input_playing_xi_df):
        """
        Utility function to simulate a set of matches using the predictive simulator
        """
        # Set up the input matches & playing XI
        data_selection_for_simulations = DataSelection(self.data_selection.historical_data_helper)
        data_selection_for_simulations.set_simulated_data(matches_df=input_matches_df,
                                                          playing_xi_df=input_playing_xi_df)

        # Setup the predictive simulator
        predictive_simulator = PredictiveSimulator(data_selection_for_simulations,
                                                   self.rewards_configuration, number_of_scenarios=1,
                                                   match_columns_to_persist=['tournament_scenario'])

        # Generate the matches & innings
        matches_df, innings_df = predictive_simulator.generate_scenario()

        # Calculate the top winners per group scenario
        winners_df = matches_df.groupby(['winner', 'tournament_scenario'])['key'].count().unstack()
        return predictive_simulator, winners_df, matches_df, innings_df

    def generate_scenarios(self):
        """
        Generate the tournament scenarios
        """
        self.validate_and_setup()

        # Play all the group stage matches
        group_input_matches_df, group_input_playing_xi_df = self.prepare_group_matches_and_players()
        logging.debug(f"Playing Group Stages: {group_input_matches_df.shape[0]} matches")
        self.group_matches_predictive_simulator, group_winners_df, group_matches_df, group_innings_df = \
            self.get_match_results(group_input_matches_df, group_input_playing_xi_df)

        # Play the Q1 & Eliminator matches
        first_non_group_input_matches_df, first_non_group_input_playing_xi_df = \
            self.prepare_q1_and_eliminator_matches_and_players(group_winners_df)
        logging.debug(f"Playing Qualifier 1 & Eliminator: "
                      f"{first_non_group_input_matches_df.shape[0]} matches")
        self.first_non_group_matches_predictive_simulator, first_non_group_winner_df, first_non_group_matches_df, \
        first_non_group_innings_df = self.get_match_results(first_non_group_input_matches_df,
                                                            first_non_group_input_playing_xi_df)

        # Play the Q2 matches
        second_non_group_input_matches_df, second_non_group_input_playing_xi_df = \
            self.prepare_q2_matches_and_players(first_non_group_matches_df)
        logging.debug(f"Playing Qualifier 2: {second_non_group_input_matches_df.shape[0]} matches")
        self.second_non_group_matches_predictive_simulator, second_non_group_winner_df, second_non_group_matches_df, \
        second_non_group_innings_df = self.get_match_results(second_non_group_input_matches_df,
                                                             second_non_group_input_playing_xi_df)

        # Play all the Final matches
        final_input_matches_df, final_input_playing_xi_df = \
            self.prepare_finals_matches_and_players(first_non_group_matches_df, second_non_group_matches_df)
        logging.debug(f"Playing Finals: {final_input_matches_df.shape[0]} matches")
        self.finals_predictive_simulator, final_winner_df, final_matches_df, final_innings_df \
            = self.get_match_results(final_input_matches_df, final_input_playing_xi_df)

        # Put together all the matches in one go
        all_matches = pd.concat([group_matches_df, first_non_group_matches_df, second_non_group_matches_df,
                                 final_matches_df])

        self.scenario_date_time = datetime.now()
        logging.debug(f"Done with tournament")

        return all_matches

    def get_rewards(self, granularity):
        """
        Get the rewards corresponding to all the matches in the tournament for the specific granularity
        """
        logging.debug("Getting Group Rewards")

        columns_to_persist = ['tournament_scenario']
        group_rewards_df = self.group_matches_predictive_simulator.get_rewards(0, granularity, columns_to_persist)

        logging.debug("Getting Q1 & Eliminator Rewards")

        first_non_group_rewards_df = self.first_non_group_matches_predictive_simulator.get_rewards(
            0, granularity, columns_to_persist=columns_to_persist)

        logging.debug("Getting Q2 Rewards")
        second_non_group_rewards_df = self.second_non_group_matches_predictive_simulator.get_rewards(
            0, granularity, columns_to_persist=columns_to_persist)

        logging.debug("Getting Finals Rewards")

        final_rewards_df = self.finals_predictive_simulator.get_rewards(
            0, granularity, columns_to_persist=columns_to_persist)

        indices = list(group_rewards_df.index.names)
        rewards_df = pd.concat([group_rewards_df, first_non_group_rewards_df, second_non_group_rewards_df,
                                final_rewards_df])
        rewards_df = rewards_df.groupby(indices).sum()
        rewards_df = rewards_df.reset_index()
        rewards_df = self.data_selection.merge_with_players(rewards_df, 'player_key')

        if 'match_key' in indices:
            rewards_df['match_key'] = \
                (rewards_df['match_key'] - (
                        rewards_df['match_key'] % self.max_number_of_scenarios)) / self.max_number_of_scenarios
            rewards_df['match_key'] = rewards_df['match_key'].astype(int)

        rewards_df.set_index(indices, inplace=True, verify_integrity=True)

        return rewards_df
