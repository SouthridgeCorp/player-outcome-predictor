import scipy.stats as sps
import pandas as pd
import numpy as np

class PredictiveUtils:
    def __init__(self, number_of_scenarios):
        self.random_number_list = list(np.random.randint(low = 3, size=number_of_scenarios))

    def predict_toss_winner(self, matches_df: pd.DataFrame, scenario_number: int):

        toss_won_by_team1_probability = sps.bernoulli(p=0.5)
        toss_won_by_team1_outcome_by_matches = toss_won_by_team1_probability.rvs(
            len(matches_df.index), random_state=self.random_number_list[scenario_number - 1])
        matches_df['predicted_team_1_won_toss'] = toss_won_by_team1_outcome_by_matches

        mask = matches_df['predicted_team_1_won_toss'] == 1
        matches_df.loc[mask, 'predicted_toss_winner'] = matches_df['team1']
        matches_df.loc[~mask, 'predicted_toss_winner'] = matches_df['team2']