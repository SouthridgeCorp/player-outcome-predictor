import pandas as pd
import pytest
import os
import random
from inferential_models.bowling_outcomes_models.first_innings_by_ball_model import sample_model
import pymc as pm
import aesara.tensor as at

def test_model(simulate_match_data):
    bowling_outcomes_by_ball_and_innings_df, \
    match_state_by_ball_and_innings_df, \
    player_id, \
    bowling_outcomes_index = simulate_match_data
    trace = sample_model(bowling_outcomes_by_ball_and_innings_df,
                         match_state_by_ball_and_innings_df,
                         player_id,
                         bowling_outcomes_index)
    assert False

def test_dummy_model(simulate_fake_data):
    batter_rv, bowling_outcome_encoded_rv, bowling_outcome_rv = simulate_fake_data
    train_idx = 120
    num_batters = batter_rv.shape[1]
    num_outcomes = bowling_outcome_encoded_rv.shape[1]

    with pm.Model() as model:
        batter_id_by_ball_and_innings_data = pm.MutableData('batter_id_by_ball_and_innings_data',
                                                            batter_rv[:train_idx])
        bowling_outcomes_by_ball_and_innings_data = pm.MutableData('bowling_outcomes_by_ball_and_innings_data',
                                                                   bowling_outcome_rv[:train_idx])
        alpha_bowling_outcome_rv = pm.Normal('alpha_bowling_outcome',
                                             mu=0,
                                             sigma=1,
                                             shape=num_outcomes)
        beta_for_batter_id_and_bowling_outcome_rv = pm.Normal('beta_for_batter_id_and_bowling_outcome',
                                                              mu=0,
                                                              sigma=1,
                                                              shape=(num_batters, num_outcomes))
        mu_bowling_outcomes = pm.Deterministic('mu_bowling_outcomes',
                                               at.dot(batter_id_by_ball_and_innings_data,
                                                      beta_for_batter_id_and_bowling_outcome_rv) + alpha_bowling_outcome_rv)
        probability_of_bowling_outcome = pm.Deterministic('probability_of_bowling_outcome',
                                                          at.nnet.softmax(mu_bowling_outcomes))
        bowling_outcomes_by_ball_and_innings_rv = pm.Categorical('bowling_outcomes_by_ball_and_innings_rv',
                                                                 p=probability_of_bowling_outcome,
                                                                 observed=bowling_outcomes_by_ball_and_innings_data)
        RANDOM_SEED = 3456
        inf_data = pm.sample(random_seed=RANDOM_SEED)
        pm.set_data({
            'batter_id_by_ball_and_innings_data': batter_rv[train_idx:]
        })
        inf_data = pm.sample_posterior_predictive(
            inf_data,
            predictions=True,
            extend_inferencedata=True,
            random_seed=RANDOM_SEED,
        )
