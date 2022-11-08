import numpy as np
import pandas as pd
import pymc as pm
from sklearn.preprocessing import OneHotEncoder
import aesara.tensor as at
from simulators.perfect_simulator import PerfectSimulator

def sample_model(bowling_outcomes_by_ball_and_innings_df,
                 match_state_by_ball_and_innings_df,
                 player_id,
                 bowling_outcomes_index):
    COORDS = {
        'player_id': player_id,
        'bowling_outcomes': bowling_outcomes_index.bowling_outcomes_index
    }

    # creating instance of one-hot-encoder
    encoder = OneHotEncoder(handle_unknown='ignore')
    batter_encoded_array = encoder.fit_transform(match_state_by_ball_and_innings_df[['batter_id']])

    outcome_encoder = OneHotEncoder(handle_unknown='ignore')
    outcome_encoded_array = outcome_encoder.fit_transform(
        bowling_outcomes_by_ball_and_innings_df[['bowling_outcome_index']])

    RANDOM_SEED = 8265

    with pm.Model(coords=COORDS) as mn_bowling_outcomes_model_by_ball_first_innings:
        with pm.Model(coords=COORDS) as cat_bowling_outcomes_model_by_ball_first_innings:
            batter_id_by_ball_and_innings_data = pm.MutableData('batter_id_by_ball_and_innings_data',
                                                                batter_encoded_array)
            bowling_outcomes_by_ball_and_innings_data = pm.MutableData('bowling_outcomes_by_ball_and_innings_data',
                                                                       bowling_outcomes_by_ball_and_innings_df[
                                                                           'bowling_outcome_index'].values)
            alpha_bowling_outcome = pm.Normal('alpha_bowling_outcome',
                                              mu=0,
                                              sigma=1,
                                              shape=bowling_outcomes_index.shape[0],
                                              initval='prior')
            beta_for_batter_id_and_bowling_outcome = pm.Normal('beta_for_batter_id_and_bowling_outcome',
                                                               mu=0,
                                                               sigma=1,
                                                               dims=('player_id', 'bowling_outcomes'),
                                                               initval='prior')
            mu_bowling_outcomes = pm.Deterministic('mu_bowling_outcomes',
                                                   at.dot(batter_id_by_ball_and_innings_data,
                                                          beta_for_batter_id_and_bowling_outcome) + alpha_bowling_outcome)
            probability_of_bowling_outcome = pm.Deterministic('probability_of_bowling_outcome',
                                                              mu_bowling_outcomes - at.logsumexp(mu_bowling_outcomes,
                                                                                                 axis=1,
                                                                                                 keepdims=True))
            bowling_outcomes_by_ball_and_innings_rv = pm.Categorical('bowling_outcomes_by_ball_and_innings_rv',
                                                                     p=probability_of_bowling_outcome,
                                                                     observed=bowling_outcomes_by_ball_and_innings_data,
                                                                     initval='prior')
            trace = pm.sample(chains=1,
                              draws=100)
            pm.sample_prior_predictive()


class FirstInningsByBallModel:
    """Class to instantiate a ball level outcomes predictor for the first innings"""

    def __init__(self,
                 perfect_simulator: PerfectSimulator):
        perfect_simulator.data_selection.
        self.all_bowling_outcomes_df = perfect_simulator.

def real_model(bowling_outcomes_by_ball_and_innings_df,
               match_state_by_ball_and_innings_df):
    bowling_outcomes_categorical = pd.Categorical(bowling_outcomes_by_ball_and_innings_df.bowling_outcome_index)
    #bowling_outcomes_idx, \
    #bowling_outcomes = bowling_outcomes_by_ball_and_innings_df.bowling_outcome_index.factorize(sort=True)
    bowling_outcomes_idx = bowling_outcomes_categorical.codes
    bowling_outcomes = bowling_outcomes_categorical.categories
    balls_idx, balls = bowling_outcomes_by_ball_and_innings_df.index.factorize(sort=True)
    COORDS = {
        "bowling_outcomes": bowling_outcomes,
        "balls": balls.tolist()
    }

    with pm.Model(coords=COORDS) as first_innings_model:
        bowling_outcomes_data = pm.MutableData("bowling_outcomes_data",
                                               bowling_outcomes_idx)
        intercept_mu = pm.Normal("intercept_mu", sigma=3.0)
        intercept_sigma = pm.HalfNormal("intercept_sigma", sigma=1.0)
        alpha_bowling_outcome_rv = pm.Normal('alpha_bowling_outcome',
                                             mu=intercept_mu,
                                             sigma=intercept_sigma,
                                             dims='bowling_outcomes')
        mu_bowling_outcome_rv = alpha_bowling_outcome_rv
        probability_of_bowling_outcome = pm.Deterministic('probability_of_bowling_outcome',
                                                          at.nnet.softmax(mu_bowling_outcome_rv))
        bowling_outcomes_by_ball_and_innings_rv = pm.Categorical('bowling_outcomes_by_ball_and_innings_rv',
                                                                 p=probability_of_bowling_outcome,
                                                                 observed=bowling_outcomes_data,
                                                                 dims = 'balls')
        idata = pm.sample()
        idata.extend(pm.sample_prior_predictive())
        idata.extend(pm.sample_posterior_predictive(idata))
        print(idata)

    return