import scipy.stats as sps
import pandas as pd

def predict_toss_winner(matches_df: pd.DataFrame, sequence_number: int):
    matches_df['toss_winning_team'] = matches_df['team2']
    toss_won_by_team1_probability = sps.bernoulli(p=0.5)
    toss_won_by_team1_outcome_by_matches = toss_won_by_team1_probability.rvs(len(matches_df.index),
                                                                             random_state=)
    matches_df.loc