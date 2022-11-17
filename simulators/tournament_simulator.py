from utils.config_utils import ConfigUtils
from data_selection.data_selection import DataSelection
from rewards_configuration.rewards_configuration import RewardsConfiguration
import pandas as pd
import logging
from simulators.predictive_simulator import PredictiveSimulator


class TournamentSimulator:

    def validate_and_setup(self):

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
            raise ValueError(f"Couldn't find some teams in the historical data.\n"
                             f"Received: {received_teams}\n"
                             f"Expected: {expected_teams}")

        # Set the match key to a sequential number > total number of historical matches
        match_key_start = matches_df['key'].max() + 1
        match_key_end = match_key_start + number_of_matches
        self.source_matches_df['key'] = range(match_key_start, match_key_end)

        # Map players to match key - assumes that the playing_xi file is sorted by matches similar to the input
        # matches file
        self.source_playing_xi_df = self.build_playing_xi(self.source_matches_df)

        # validate that the players in the source matches is available in the overall dataset
        received_players = set(self.source_playing_xi_df['player_key'].unique().tolist())
        expected_players = set(players_df['key'].unique().tolist())

        if not received_players.issubset(expected_players):
            raise ValueError(f"Couldn't find some players in the historical data.\n"
                             f"Received: {received_players}\n"
                             f"Expected: {expected_players}")

    def build_playing_xi(self, source_matches_df):
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
        self.number_of_scenarios, matches_file_name, playing_xi_file_name = config_utils.get_tournament_simulator_info()
        self.data_selection = data_selection
        self.rewards_configuration = rewards_configuration

        self.source_matches_df = pd.read_csv(matches_file_name)
        self.master_playing_xi_df = pd.read_csv(playing_xi_file_name)
        # self.master_playing_xi_df.set_index('team', inplace=True, verify_integrity=True)
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
        group_stage_matches_df = self.get_group_stage_matches()
        matches_df = pd.DataFrame()
        playing_xi_df = pd.DataFrame()
        for scenario in range(0, self.number_of_scenarios):
            matches_to_add_df = group_stage_matches_df.copy()
            matches_to_add_df['tournament_scenario'] = scenario
            matches_to_add_df['key'] = (matches_to_add_df['key'] * 10) + scenario
            matches_df = pd.concat([matches_df, matches_to_add_df])

            players_to_add_df = self.source_playing_xi_df.copy()
            players_to_add_df['match_key'] = (players_to_add_df['match_key'] * 10) + scenario
            playing_xi_df = pd.concat((playing_xi_df, players_to_add_df))

        return matches_df, playing_xi_df

    def prepare_non_group_matches(self, previous_winners_df, non_group_matches, stages):
        matches_df = pd.DataFrame()
        playing_xi_df = pd.DataFrame()
        for scenario in range(0, self.number_of_scenarios):
            matches_to_add_df = non_group_matches.copy()
            matches_to_add_df['tournament_scenario'] = scenario

            sorted_winners_df = previous_winners_df.sort_values(by=[0], ascending=False)[scenario]
            team_position = 0
            for stage in stages:
                mask = self.source_matches_df['stage'] == stage
                matches_to_add_df.loc[mask, 'team1'] = sorted_winners_df.index[team_position]
                team_position += 1
                matches_to_add_df.loc[mask, 'team2'] = sorted_winners_df.index[team_position]
                team_position += 1

            matches_to_add_df['key'] = (matches_to_add_df['key'] * 10) + scenario
            matches_df = pd.concat([matches_df, matches_to_add_df])

            players_to_add_df = self.build_playing_xi(matches_to_add_df)
            playing_xi_df = pd.concat((playing_xi_df, players_to_add_df))

        return matches_df, playing_xi_df

    def prepare_q1_and_eliminator_matches_and_players(self, previous_winners_df):
        non_group_matches = self.get_first_non_group_matches()
        return self.prepare_non_group_matches(previous_winners_df,
                                              non_group_matches,
                                              self.q1_group_stage + self.eliminator_group_stage)

    def prepare_q2_matches_and_players(self, q1_and_elim_df):
        non_group_matches = self.get_second_non_group_matches()
        previous_matches_df = q1_and_elim_df.copy()

        previous_matches_df['loser'] = previous_matches_df['team1']

        mask = (previous_matches_df['winner'] == previous_matches_df['team1'])
        previous_matches_df.loc[mask, 'loser'] = previous_matches_df['team2']

        matches_df = pd.DataFrame()
        playing_xi_df = pd.DataFrame()
        for scenario in range(0, self.number_of_scenarios):
            matches_to_add_df = non_group_matches.copy()
            matches_to_add_df['tournament_scenario'] = scenario
            mask = (previous_matches_df['stage'] == self.q1_group_stage[0]) & \
                   (previous_matches_df['tournament_scenario'] == scenario)
            matches_to_add_df['team1'] = previous_matches_df[mask]['loser'].values[0]

            mask = (previous_matches_df['stage'] == self.eliminator_group_stage[0]) & \
                   (previous_matches_df['tournament_scenario'] == scenario)
            matches_to_add_df['team2'] = previous_matches_df[mask]['winner'].values[0]

            matches_to_add_df['key'] = (matches_to_add_df['key'] * 10) + scenario
            matches_df = pd.concat([matches_df, matches_to_add_df])

            players_to_add_df = self.build_playing_xi(matches_to_add_df)
            playing_xi_df = pd.concat((playing_xi_df, players_to_add_df))

        return matches_df, playing_xi_df

    def prepare_finals_matches_and_players(self, q1_and_elim_df, q2_df):
        non_group_matches = self.get_final_matches()
        matches_df = pd.DataFrame()
        playing_xi_df = pd.DataFrame()
        for scenario in range(0, self.number_of_scenarios):
            matches_to_add_df = non_group_matches.copy()
            matches_to_add_df['tournament_scenario'] = scenario

            mask = (q1_and_elim_df['stage'] == self.q1_group_stage[0]) & \
                   (q1_and_elim_df['tournament_scenario'] == scenario)
            matches_to_add_df['team1'] = q1_and_elim_df[mask]['winner'].values[0]

            mask = q2_df['tournament_scenario'] == scenario
            matches_to_add_df['team2'] = q2_df[mask]['winner'].values[0]

            matches_to_add_df['key'] = (matches_to_add_df['key'] * 10) + scenario
            matches_df = pd.concat([matches_df, matches_to_add_df])

            players_to_add_df = self.build_playing_xi(matches_to_add_df)
            playing_xi_df = pd.concat((playing_xi_df, players_to_add_df))

        return matches_df, playing_xi_df

        return self.prepare_non_group_matches(previous_winners_df,
                                              non_group_matches,
                                              self.q2_group_stage)

    def get_match_results(self, input_matches_df, input_playing_xi_df):
        data_selection_for_simulations = DataSelection(self.data_selection.historical_data_helper)

        data_selection_for_simulations.set_simulated_data(matches_df=input_matches_df,
                                                          playing_xi_df=input_playing_xi_df)

        predictive_simulator = PredictiveSimulator(data_selection_for_simulations,
                                                   self.rewards_configuration, number_of_scenarios=1,
                                                   match_columns_to_persist=['tournament_scenario'])
        matches_df, innings_df = predictive_simulator.generate_scenario()
        winners_df = matches_df.groupby(['winner', 'tournament_scenario'])['key'].count().unstack()

        return predictive_simulator, winners_df, matches_df, innings_df

    def generate_scenarios(self):
        self.validate_and_setup()

        # Play all the group stage matches
        group_input_matches_df, group_input_playing_xi_df = self.prepare_group_matches_and_players()
        logging.debug(f"******************* Playing Group Stages: {group_input_matches_df.shape[0]} matches")
        self.group_matches_predictive_simulator, group_winners_df, group_matches_df, group_innings_df = \
            self.get_match_results(group_input_matches_df, group_input_playing_xi_df)

        first_non_group_input_matches_df, first_non_group_input_playing_xi_df = \
            self.prepare_q1_and_eliminator_matches_and_players(group_winners_df)
        logging.debug(f"******************* Playing Qualifier 1 & Eliminator: "
                      f"{first_non_group_input_matches_df.shape[0]} matches")
        self.first_non_group_matches_predictive_simulator, first_non_group_winner_df, first_non_group_matches_df, \
        first_non_group_innings_df = self.get_match_results(first_non_group_input_matches_df,
                                                            first_non_group_input_playing_xi_df)

        second_non_group_input_matches_df, second_non_group_input_playing_xi_df = \
            self.prepare_q2_matches_and_players(first_non_group_matches_df)
        logging.debug(f"******************* Playing Qualifier 2: {second_non_group_input_matches_df.shape[0]} matches")
        self.second_non_group_matches_predictive_simulator, second_non_group_winner_df, second_non_group_matches_df, \
        second_non_group_innings_df = self.get_match_results(second_non_group_input_matches_df,
                                                             second_non_group_input_playing_xi_df)

        final_input_matches_df, final_input_playing_xi_df = \
            self.prepare_finals_matches_and_players(first_non_group_matches_df, second_non_group_matches_df)
        logging.debug(f"******************* Playing Finals: {final_input_matches_df.shape[0]} matches")
        self.finals_predictive_simulator, final_winner_df, final_matches_df, final_innings_df \
            = self.get_match_results(final_input_matches_df, final_input_playing_xi_df)

        all_matches = pd.concat([group_matches_df, first_non_group_matches_df, second_non_group_matches_df,
                                 final_matches_df])

        logging.debug(f"Done with tournament")
        return all_matches
