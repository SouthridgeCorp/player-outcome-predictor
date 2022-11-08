import scipy.stats as sps
from data_selection.data_selection import DataSelection
from rewards_configuration.rewards_configuration import RewardsConfiguration
from simulators.utils.predictive_utils import PredictiveUtils
import pandas as pd


class PredictiveSimulator:

    def __init__(self, data_selection: DataSelection,
                 rewards_configuration: RewardsConfiguration,
                 number_of_scenarios):
        self.data_selection = data_selection
        self.number_of_scenarios = number_of_scenarios
        self.predictive_utils = PredictiveUtils(self.number_of_scenarios)

    def generate_scenario(self):
        matches_df = self.data_selection.get_selected_matches(True)
        self.predictive_utils.setup_with_matches(matches_df)
        matches_df.set_index('key', inplace=True)

        for i in range(0, self.number_of_scenarios):
            self.predict_selected_matches(scenario_number=i, matches_df=matches_df)

    def predict_selected_matches(self, scenario_number: int, matches_df: pd.DataFrame) -> pd.DataFrame:
        matches_for_scenario_df = matches_df.copy()
        self.predictive_utils.predict_toss_winner(scenario_number, matches_for_scenario_df)
        self.predictive_utils.predict_toss_winner_action(matches_for_scenario_df, scenario_number)
        return matches_for_scenario_df

