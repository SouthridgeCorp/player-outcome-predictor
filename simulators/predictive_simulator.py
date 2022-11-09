import scipy.stats as sps
from data_selection.data_selection import DataSelection
from rewards_configuration.rewards_configuration import RewardsConfiguration
from simulators.utils.predictive_utils import PredictiveUtils


class PredictiveSimulator:

    def __init__(self, data_selection: DataSelection,
                 rewards_configuration: RewardsConfiguration,
                 number_of_scenarios):
        self.data_selection = data_selection
        self.number_of_scenarios = number_of_scenarios
        self.predictive_utils = PredictiveUtils(self.number_of_scenarios)
        self.matches_df = self.data_selection.get_selected_matches(True)

    def generate_sequence(self):
        pass

    def predict_selected_matches(self, scenario_number: int):
        self.matches_df.set_index('key', inplace=True)
        self.predictive_utils.predict_toss_winner(self.matches_df, scenario_number)
        return self.matches_df
