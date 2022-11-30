from data_selection.data_selection import DataSelection
from inferential_models.batter_runs_models import BatterRunsModel
from rewards_configuration.rewards_configuration import RewardsConfiguration
from simulators.utils.predictive_utils import PredictiveUtils, update_match_state
from simulators.perfect_simulator import PerfectSimulator
from simulators.utils.predictive_match_state import MatchState
import pandas as pd
import logging
import datetime


class PredictiveSimulator:
    """
    Predicts the outcomes of the testing set of matches across the specified number of scenarios.
    """

    def __init__(self,
                 data_selection: DataSelection,
                 rewards_configuration: RewardsConfiguration,
                 batter_runs_model: BatterRunsModel,
                 number_of_scenarios,
                 match_columns_to_persist=[],
                 utils=None):
        self.data_selection = data_selection
        self.number_of_scenarios = number_of_scenarios
        self.rewards_configuration = rewards_configuration

        if utils is None:
            self.predictive_utils = PredictiveUtils(data_selection,
                                                    batter_runs_model)
        else:
            self.predictive_utils = utils

        self.perfect_simulators = []
        self.simulated_matches_df = pd.DataFrame()
        self.simulated_innings_df = pd.DataFrame()

        self.match_columns_to_persist = match_columns_to_persist

        # Maintain a perfect simulator for each scenario which allows us to calculate the rewards & error metrics
        # per scenario easily
        for i in range(0, number_of_scenarios):
            perfect_simulator_ds = DataSelection(data_selection.historical_data_helper)
            self.perfect_simulators.append(PerfectSimulator(perfect_simulator_ds, rewards_configuration))

        self.scenario_date_time = None

    def generate_matches(self):
        """
        Generates the matches dataframe corresponding to the match set to simulate.
        """
        matches_df = self.data_selection.get_selected_matches(True)
        simulated_matches_df = pd.DataFrame()
        number_of_matches = len(matches_df.index)

        # Build a list of matches for each scenario
        for i in range(0, self.number_of_scenarios):
            scenario = {'scenario_number': i,
                        'key': matches_df['key'].values.tolist(),
                        'match_key': matches_df['key'].values.tolist(),
                        'tournament_key': matches_df['tournament_key'].values.tolist(),
                        'date': matches_df['date'].values.tolist(),
                        'stage': matches_df['stage'].values.tolist(),
                        'venue': matches_df['venue'].values.tolist(),
                        'team1': matches_df['team1'].values.tolist(),
                        'team2': matches_df['team2'].values.tolist()
                        }
            for column in self.match_columns_to_persist:
                scenario[column] = matches_df[column].values.tolist()
            scenario_df = pd.DataFrame(scenario)
            simulated_matches_df = pd.concat([simulated_matches_df, scenario_df], ignore_index=True)

        # Set up the toss results - toss winner & their decision (field or bat)
        self.predictive_utils.compute_toss_results(simulated_matches_df, self.number_of_scenarios, number_of_matches)

        simulated_matches_df.set_index(['scenario_number', 'match_key'], inplace=True, verify_integrity=True)
        return simulated_matches_df

    def initialise_match_state(self, row, match_state_dict, playing_xi_df):
        """
        Internal helper function - not to be used outside this class.
        Iniatialises the match state objects for each match & scenario
        """
        scenario = row.name[0]
        match_key = row.name[1]
        batting_team = row['batting_team']
        bowling_team = row['bowling_team']
        venue = row['venue']
        batting_playing_xi = playing_xi_df.query(f'match_key == {match_key} and '
                                                 f'team == "{batting_team}"')['player_key'].to_list()
        bowling_playing_xi = playing_xi_df.query(f'match_key == {match_key} and '
                                                 f'team == "{bowling_team}"')['player_key'].to_list()
        match_state = MatchState(self.predictive_utils, scenario, match_key, bowling_team,
                                 batting_team, batting_playing_xi, bowling_playing_xi, venue)
        match_state_dict[(scenario, match_key)] = match_state

    def generate_innings(self, use_inferential_model):
        logging.debug("Getting playing xi")
        playing_xi_df = self.data_selection.get_playing_xi_for_selected_matches(True)
        simulated_innings_df = pd.DataFrame()

        logging.debug("Initialising match state")
        match_state_dict = {}
        self.simulated_matches_df.apply(lambda x: self.initialise_match_state(x, match_state_dict, playing_xi_df),
                                        axis=1)

        logging.debug(f"Starting to play {len(self.simulated_matches_df.index)} matches")
        for inning in [1, 2]:
            over = -1
            ball = 0
            while True:
                ball += 1
                if (over == -1) or (ball == 7):
                    over += 1
                    ball = 1
                    over_changed = True
                else:
                    over_changed = False
                if over == 20:
                    break
                logging.info(f"Playing inning {inning}, over {over}, ball {ball}")
                for key in match_state_dict.keys():
                    match_state = match_state_dict[key]
                    match_state.set_innings(inning)
                    if over_changed:
                        match_state.change_over()
                    else:
                        match_state.bowl_one_ball()

                simulated_innings_df = self.play_one_ball(match_state_dict,
                                                          simulated_innings_df,
                                                          use_inferential_model)

                extras_list_to_consider = match_state_dict
                while True:
                    extras_list = {}
                    for key in extras_list_to_consider.keys():
                        if match_state_dict[key].was_previous_non_legal_delivery():
                            extras_list[key] = match_state_dict[key]
                            match_state_dict[key].bowl_one_ball()
                    if len(extras_list.keys()) == 0:
                        break
                    if extras_list == extras_list_to_consider:
                        extras_list_to_consider = {}
                    else:
                        extras_list_to_consider = extras_list

                    simulated_innings_df = self.play_one_ball(extras_list,
                                                              simulated_innings_df,
                                                              use_inferential_model)
        logging.debug("Done playing all matches")
        return simulated_innings_df

    def play_one_ball(self,
                      match_state_dict,
                      simulated_innings_df,
                      use_inferential_model):
        """
        This function doest the following:
        - builds out the dataframe representing the current match state for all matches & scenarios
        - passes the current state df to a predictor which informs what the outcome of that ball is
        - updates all the match state objects with the status of the ball outcome
        - appends the ball outcome information to the simulated innings dataframe so we can keep a record
        """

        # Get a dictionary view of the current state of all the matches
        match_state_per_scenario_list = []
        for key in match_state_dict.keys():
            match_dict = match_state_dict[key].get_dict()
            if len(match_dict.keys()) != 0:
                match_state_per_scenario_list.append(match_dict)

        if len(match_state_per_scenario_list) > 0:
            # Build out the current state dataframe
            match_state_df = pd.DataFrame(match_state_per_scenario_list)
            match_state_df.set_index(['scenario_number', 'match_key', 'inning', 'over', 'ball'], inplace=True,
                                     verify_integrity=True)
            match_state_df = match_state_df.sample(frac=1)

            # Predict ball by ball outcome
            self.predictive_utils.predict_ball_by_ball_outcome(match_state_df,
                                                               use_inferential_model)
            match_state_df['total_runs'] = match_state_df['batter_runs'] + match_state_df['extras']

            # Apply the current state outcomes to the match state objects
            match_state_df['fielder'] = match_state_df.apply(
                lambda x: update_match_state(x, match_state_dict), axis=1)

            # Keep a record of this ball in innings_df
            simulated_innings_df = pd.concat([simulated_innings_df, match_state_df])

        return simulated_innings_df

    def generate_scenario(self,
                          use_inferential_model=False):
        """
        Generate all the required scenarios
        """
        logging.debug("Setting up scenario state")

        self.predictive_utils.setup(use_inferential_model)

        logging.debug("Generating simulated Match data")

        self.simulated_matches_df = self.generate_matches()

        logging.debug("Generating simulated Innings data")
        self.simulated_innings_df = self.generate_innings(use_inferential_model)

        self.calculate_match_winner()

        # Set up the matches & innings in each of the perfect simulators for future counting
        self.simulated_matches_df = self.simulated_matches_df.reset_index()
        self.simulated_innings_df = self.simulated_innings_df.reset_index()
        for i in range(0, self.number_of_scenarios):
            perfect_simulator = self.perfect_simulators[i]
            perfect_simulator.data_selection.set_simulated_data(
                self.simulated_matches_df[self.simulated_matches_df['scenario_number'] == i],
                self.simulated_innings_df[self.simulated_innings_df['scenario_number'] == i])

        self.simulated_matches_df.set_index(['scenario_number', 'match_key'], inplace=True, verify_integrity=True)
        self.simulated_innings_df.set_index(['scenario_number', 'match_key', 'inning', 'over', 'ball'], inplace=True,
                                            verify_integrity=True)

        self.scenario_date_time = datetime.datetime.now()

        logging.debug("Done Generating Match & Innings data")

        return self.simulated_matches_df, self.simulated_innings_df

    def calculate_match_winner(self):
        """
        Calculate the winner & loser for a match, and update the innings
        """
        winner_df = self.simulated_innings_df.reset_index().groupby(['scenario_number', 'match_key']).last()

        # TODO: Update with logic for ties. Currently the bowling team wins if the scores are tied
        winner_df['winner'] = winner_df['bowling_team']
        mask = (winner_df['previous_total'] + winner_df['total_runs']) >= winner_df['target_runs']
        winner_df.loc[mask, 'winner'] = winner_df['batting_team']

        winner_df['loser'] = winner_df['bowling_team']

        mask = (winner_df['winner'] == winner_df['bowling_team'])
        winner_df.loc[mask, 'loser'] = winner_df['batting_team']

        self.simulated_matches_df = pd.merge(self.simulated_matches_df, winner_df[['winner', 'loser']],
                                             left_index=True, right_index=True)

    def get_rewards(self, scenario, granularity, columns_to_persist=[]) -> pd.DataFrame:
        """
        Returns the rewards dataframe for the specific scenario
        @param scenario: The scenario # for whcih to return the rewards config for
        @param granularity: The granularity for calculating the rewards config
        @param columns_to_persist: The list of columns to persist in the output dataframes
        @return The rewards dataframe corresponding to the expected scenario
        """
        return self.perfect_simulators[scenario].get_simulation_evaluation_metrics_by_granularity(
            True, granularity, columns_to_persist=columns_to_persist)

    def __str__(self):
        """String representation of this class, can be used with print, st.write etc"""
        return f"Predictive Simulator:  " \
               f"Scenario last generated at {self.scenario_date_time}  " \
               f"{self.predictive_utils.batter_runs_model}  "

    def get_error_stats(self, granularity):
        """
        Generate the error differential between the predicted matches & the perfect simulator, across all possible
        """
        data_selection_combined = DataSelection(self.data_selection.historical_data_helper)
        perfect_simulator_combined = PerfectSimulator(data_selection_combined, self.rewards_configuration)

        matches_df = self.simulated_matches_df.copy()
        innings_df = self.simulated_innings_df.copy()
        max_number_of_scenarios = 100

        matches_df = matches_df.reset_index()
        innings_df = innings_df.reset_index()

        matches_df["key"] = (matches_df["key"] * max_number_of_scenarios) + matches_df['scenario_number']
        matches_df["match_key"] = (matches_df["match_key"] * max_number_of_scenarios) + matches_df['scenario_number']

        innings_df["match_key"] = (innings_df["match_key"] * max_number_of_scenarios) + innings_df['scenario_number']

        perfect_simulator_combined.data_selection.set_simulated_data(matches_df, innings_df)

        columns_to_persist = ['scenario_number']

        metrics_df = perfect_simulator_combined.get_simulation_evaluation_metrics_by_granularity(
            True, granularity, columns_to_persist=columns_to_persist)

        perfect_simulator = PerfectSimulator(self.data_selection, self.rewards_configuration)
        perfect_metrics_df = perfect_simulator.get_simulation_evaluation_metrics_by_granularity(
            True, granularity)

        perfect_metrics_index = list(perfect_metrics_df.index.names)

        perfect_metrics_df = perfect_metrics_df.reset_index()

        perfect_metrics_df = (perfect_metrics_df.loc[perfect_metrics_df.index.repeat(self.number_of_scenarios)]
                              .assign(scenario_number=lambda d: d.groupby(level=0).cumcount())
                              .reset_index(drop=True)
                              )
        if 'match_key' in perfect_metrics_index:
            perfect_metrics_df['match_key'] = (perfect_metrics_df['match_key'] * max_number_of_scenarios) \
                                              + perfect_metrics_df['scenario_number']

        perfect_metrics_df.set_index(perfect_metrics_index + ['scenario_number'], inplace=True, verify_integrity=True)


        error_df = perfect_simulator.get_error_measures(True, metrics_df, granularity,
                                                        perfect_simulator_rewards_ref=perfect_metrics_df,
                                                        columns_to_persist=columns_to_persist)

        indices = list(error_df.index.names)
        error_df = error_df.reset_index()
        if 'match_key' in indices:
            error_df['match_key'] = \
                (error_df['match_key'] - (error_df['match_key'] % max_number_of_scenarios)) / max_number_of_scenarios
            error_df['match_key'] = error_df['match_key'].astype(int)

        error_df.set_index(indices, inplace=True, verify_integrity=True)
        return error_df


