import scipy.stats as sps
from data_selection.data_selection import DataSelection
from rewards_configuration.rewards_configuration import RewardsConfiguration
from simulators.utils.predictive_utils import PredictiveUtils
from simulators.perfect_simulator import PerfectSimulator
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
                        'toss_decision': 'bat'}
            scenario_df = pd.DataFrame(scenario)

            simulated_matches_df = pd.concat([simulated_matches_df, scenario_df], ignore_index=True)

        self.predictive_utils.compute_toss_results(simulated_matches_df, self.number_of_scenarios, number_of_matches)

        return simulated_matches_df

    def generate_innings(self):
        simulated_innings_df = self.simulated_matches_df.copy()
        playing_xi_df = self.data_selection.get_playing_xi_for_selected_matches(True)
        for i in range(0, self.number_of_scenarios):
            pass #simulated_innings_df['inning'] =

        return simulated_innings_df


    def generate_scenario(self):
        self.simulated_matches_df = self.generate_matches()
        self.simulated_innings_df = self.generate_innings()

        for i in range(0, self.number_of_scenarios):
            perfect_simulator = self.perfect_simulators[i]
            perfect_simulator.data_selection.set_simulated_data(
                self.simulated_matches_df[self.simulated_matches_df['scenario_number'] == i],
                self.simulated_innings_df[self.simulated_innings_df['scenario_number'] == i])

    #def predict_selected_matches(self, scenario_number: int, matches_df: pd.DataFrame) -> pd.DataFrame:
     #   matches_for_scenario_df = matches_df.copy()
      #  self.predictive_utils.predict_toss_winner(scenario_number, matches_for_scenario_df)
       # self.predictive_utils.predict_toss_winner_action(matches_for_scenario_df, scenario_number)
        #return matches_for_scenario_df

