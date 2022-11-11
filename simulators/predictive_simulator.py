import scipy.stats as sps
from data_selection.data_selection import DataSelection
from rewards_configuration.rewards_configuration import RewardsConfiguration
from simulators.utils.predictive_utils import PredictiveUtils, update_match_state
from simulators.perfect_simulator import PerfectSimulator
from simulators.utils.predictive_utils import MatchState
import pandas as pd


class PredictiveSimulator:

    def __init__(self, data_selection: DataSelection,
                 rewards_configuration: RewardsConfiguration,
                 number_of_scenarios):
        self.data_selection = data_selection
        self.number_of_scenarios = number_of_scenarios
        self.predictive_utils = PredictiveUtils(data_selection)
        self.perfect_simulators = []
        self.simulated_matches_df = pd.DataFrame()
        self.simulated_innings_df = pd.DataFrame()
        for i in range(0, number_of_scenarios):
            perfect_simulator_ds = DataSelection(data_selection.historical_data_helper)
            self.perfect_simulators.append(PerfectSimulator(perfect_simulator_ds, rewards_configuration))

    def generate_matches(self):
        matches_df = self.data_selection.get_selected_matches(True)
        simulated_matches_df = pd.DataFrame()
        number_of_matches = len(matches_df.index)

        for i in range(0, self.number_of_scenarios):
            scenario = {'scenario_number': i,
                        'match_key': matches_df['key'].values.tolist(),
                        'tournament_key': matches_df['tournament_key'].values.tolist(),
                        'date': matches_df['date'].values.tolist(),
                        'stage': matches_df['stage'].values.tolist(),
                        'venue': matches_df['venue'].values.tolist(),
                        'team1': matches_df['team1'].values.tolist(),
                        'team2': matches_df['team2'].values.tolist(),
                        'toss_winner': matches_df['team2'].values.tolist(),
                        'toss_loser': matches_df['team1'].values.tolist(),
                        'toss_decision': 'bat'}
            scenario_df = pd.DataFrame(scenario)

            simulated_matches_df = pd.concat([simulated_matches_df, scenario_df], ignore_index=True)

        self.predictive_utils.compute_toss_results(simulated_matches_df, self.number_of_scenarios, number_of_matches)
        simulated_matches_df.set_index(['scenario_number', 'match_key'], inplace=True, verify_integrity=True)
        return simulated_matches_df

    def generate_innings(self):
        playing_xi_df = self.data_selection.get_playing_xi_for_selected_matches(True)
        simulated_innings_df = pd.DataFrame()

        match_state_dict = {}

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
                for scenario, matches_df in self.simulated_matches_df.groupby('scenario_number'):
                    for match_key, match_df in matches_df.groupby('match_key'):
                        if (scenario, match_key) in match_state_dict.keys():
                            match_state = match_state_dict[(scenario, match_key)]
                        else:
                            batting_team = match_df.iloc[0]['batting_team']
                            bowling_team = match_df.iloc[0]['bowling_team']
                            batting_playing_xi = playing_xi_df.query(f'match_key == {match_key} and '
                                                                     f'team == "{batting_team}"')['player_key'].to_list()
                            bowling_playing_xi = playing_xi_df.query(f'match_key == {match_key} and '
                                                                     f'team == "{bowling_team}"')['player_key'].to_list()
                            match_state = MatchState(self.predictive_utils, scenario, match_key, bowling_team,
                                                     batting_team, batting_playing_xi, bowling_playing_xi)
                            match_state_dict[(scenario, match_key)] = match_state

                        match_state.set_innings(inning)
                        if over_changed:
                            match_state.change_over()
                        else:
                            match_state.bowl_one_ball()

                match_state_per_scenario_list = []
                for key in match_state_dict.keys():
                    match_dict_list = match_state_dict[key].get_dict_list()
                    for match_dict in match_dict_list:
                        if len(match_dict.keys()) != 0:
                            match_state_per_scenario_list.append(match_dict)

                if len(match_state_per_scenario_list) > 0:
                    match_state_df = pd.DataFrame(match_state_per_scenario_list)
                    match_state_df.set_index(['scenario_number', 'match_key', 'inning', 'over', 'ball'], inplace=True,
                                             verify_integrity=True)

                    self.predictive_utils.predict_ball_by_ball_outcome(match_state_df)

                    match_state_df.apply(
                        lambda x: update_match_state(x, match_state_dict), axis=1)
                    simulated_innings_df = pd.concat([simulated_innings_df, match_state_df])


        #simulated_innings_df = pd.DataFrame(innings_list)
        return simulated_innings_df

    def generate_scenario(self):
        self.predictive_utils.setup()


        self.simulated_matches_df = self.generate_matches()
        self.simulated_innings_df = self.generate_innings()

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