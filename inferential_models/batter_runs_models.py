import numpy as np
import pandas as pd
import pymc as pm
from sklearn.preprocessing import OneHotEncoder
import aesara.tensor as at
from simulators.perfect_simulator import PerfectSimulator
import pickle

RANDOM_SEED = 8265

def load_idata_trained(model_path):
    with open(f'data/inferential_models/{model_path}.pkl', 'rb') as buff:
        data = pickle.load(buff)
    idata = data['trace']
    return idata

def get_batter_runs_model(idata_trained):
    COORDS = {
        'batter_runs': idata_trained.posterior.batter_runs.values,
        'batter_featured_id': idata_trained.posterior.batter_featured_id.values,
        'bowler_featured_id': idata_trained.posterior.bowler_featured_id.values,
        'over': idata_trained.posterior.over.values,
        'venue': idata_trained.posterior.venue.values,
        'wickets_fallen': idata_trained.posterior.wickets_fallen.values,
        'inning': idata_trained.posterior.inning.values,
        'is_wicket': idata_trained.posterior.is_wicket.values,
        'is_legal_delivery': idata_trained.posterior.is_legal_delivery.values
    }
    with pm.Model(coords=COORDS) as model:
        model.add_coord('ball_ids',
                        values=idata_trained.constant_data.ball_ids.values,
                        mutable=True)
        batter_runs_outcomes_data = pm.MutableData("batter_runs_outcomes_data",
                                                   idata_trained.constant_data['batter_runs_outcomes_data'],
                                                   dims='ball_ids')
        batter_runs_outcome_alpha_by_inning = pm.Normal('batter_runs_outcome_alpha_by_inning',
                                                        mu=0,
                                                        sigma=3.0,
                                                        dims=('inning',
                                                              'batter_runs'))
        batter_featured_id_feature_data = pm.MutableData("batter_featured_id_feature_data",
                                                         idata_trained.constant_data['batter_featured_id_feature_data'],
                                                         dims='ball_ids')
        bowler_featured_id_feature_data = pm.MutableData("bowler_featured_id_feature_data",
                                                         idata_trained.constant_data['bowler_featured_id_feature_data'],
                                                         dims='ball_ids')
        venue_feature_data = pm.MutableData("venue_feature_data",
                                            idata_trained.constant_data['venue_feature_data'],
                                            dims='ball_ids')
        over_feature_data = pm.MutableData("over_feature_data",
                                           idata_trained.constant_data['over_feature_data'],
                                           dims='ball_ids')
        wickets_fallen_feature_data = pm.MutableData("wickets_fallen_feature_data",
                                                     idata_trained.constant_data['wickets_fallen_feature_data'],
                                                     dims='ball_ids')
        innings_strike_rate_feature_data = pm.MutableData("innings_strike_rate_feature_data",
                                                          idata_trained.constant_data['innings_strike_rate_feature_data'])
        batter_runs_outcome_alpha = pm.Normal('batter_runs_outcome_alpha',
                                              mu=0,
                                              sigma=3,
                                              dims='batter_runs')
        batter_runs_outcome_alpha_by_over = pm.Normal('batter_runs_outcome_alpha_by_over',
                                                      mu=0,
                                                      sigma=3.0,
                                                      dims=('over',
                                                            'batter_runs'))
        batter_runs_outcome_alpha_mu_by_batter_global = 0
        batter_runs_outcome_alpha_sigma_by_batter_global = 3.0
        batter_runs_outcome_alpha_by_batter = pm.Normal('batter_runs_outcome_alpha_by_batter',
                                                        mu=batter_runs_outcome_alpha_mu_by_batter_global,
                                                        sigma=batter_runs_outcome_alpha_sigma_by_batter_global,
                                                        dims=('batter_featured_id',
                                                              'batter_runs'))
        batter_runs_outcome_alpha_by_bowler = pm.Normal('batter_runs_outcome_alpha_by_bowler',
                                                        mu=0,
                                                        sigma=3.0,
                                                        dims=('bowler_featured_id',
                                                              'batter_runs'))
        batter_runs_outcome_alpha_by_venue = pm.Normal('batter_runs_outcome_alpha_by_venue',
                                                       mu=0,
                                                       sigma=3.0,
                                                       dims=('venue',
                                                             'batter_runs'))

        batter_runs_outcome_alpha_by_wickets_fallen = pm.Normal('batter_runs_outcome_alpha_by_wickets_fallen',
                                                                mu=0,
                                                                sigma=3.0,
                                                                dims=('wickets_fallen',
                                                                      'batter_runs'))
        batter_runs_outcome_beta_by_innings_strike_rate = pm.Normal("beta",
                                                                    mu=0,
                                                                    sigma=1,
                                                                    shape=(1,
                                                                           COORDS['batter_runs'].shape[0]))
        batter_runs_outcome_alpha_by_is_wicket = pm.Normal('batter_runs_outcome_alpha_by_is_wicket',
                                                           mu=0,
                                                           sigma=3.0,
                                                           dims=('is_wicket',
                                                                 'batter_runs'))
        batter_runs_outcome_alpha_by_is_legal_delivery = pm.Normal('batter_runs_outcome_alpha_by_is_legal_delivery',
                                                                   mu=0,
                                                                   sigma=3.0,
                                                                   dims=('is_legal_delivery',
                                                                         'batter_runs'))
        batter_runs_outcome_mu = pm.Deterministic('mu_batter_runs_outcome_rv',
                                                  batter_runs_outcome_alpha +
                                                  batter_runs_outcome_alpha_by_batter[batter_featured_id_feature_data] +
                                                  batter_runs_outcome_alpha_by_bowler[bowler_featured_id_feature_data] +
                                                  batter_runs_outcome_alpha_by_over[over_feature_data] +
                                                  batter_runs_outcome_alpha_by_wickets_fallen[
                                                      wickets_fallen_feature_data] +
                                                  batter_runs_outcome_beta_by_innings_strike_rate * innings_strike_rate_feature_data +
                                                  batter_runs_outcome_alpha_by_venue[venue_feature_data])
        probability_of_batter_runs_outcome_rv = pm.Deterministic('probability_of_batter_runs_outcome',
                                                                 at.nnet.softmax(batter_runs_outcome_mu),
                                                                 dims=('ball_ids', 'batter_runs'))
        batter_outcomes_by_ball_and_innings_rv = pm.Categorical('batter_runs_outcome_by_ball_and_innings_rv',
                                                                p=probability_of_batter_runs_outcome_rv,
                                                                observed=batter_runs_outcomes_data,
                                                                dims='ball_ids')
    return model

def get_categorical_column_index_for_df(df,
                                        categories,
                                        column):
    transformed_column_name = column.split('_')[0] if 'featured_id' in column else column
    if transformed_column_name == 'wickets_fallen' and 'wickets_fallen' not in df:
        transformed_column_name = 'previous_number_of_wickets'
    idx = pd.Categorical(df[transformed_column_name],
                         categories).codes
    return idx


def innings_strike_rate(df):
    if 'current_total' in df and 'total_ball_bowled' in df:
        df['innings_strike_rate'] = df['current_total'] / df['total_balls_bowled']
    else:
        df['innings_strike_rate'] = df['previous_total'] / (df['over']*6 + df['ball'])
    df['innings_strike_rate'].fillna(0, inplace=True)
    max_value = np.nanmax(df[['innings_strike_rate']][df['innings_strike_rate'] != np.inf])
    df['innings_strike_rate'].replace([np.inf, -np.inf], max_value, inplace=True)


def add_column_to_df(df,
                     column_name):
    column_name(df)

def prepare_match_state_df(match_state_df,
                           idata_trained):

    feature_data = {}
    for dim in ['batter_featured_id',
                'bowler_featured_id',
                'venue',
                'wickets_fallen',
                'over',
                'inning']:
        categories = idata_trained.posterior[dim].values
        feature_data[dim] = get_categorical_column_index_for_df(match_state_df,
                                                                categories,
                                                                dim)

    for column in [innings_strike_rate]:
        add_column_to_df(match_state_df,
                         column)

    for dim in ['innings_strike_rate']:
        feature_data[dim] = match_state_df[dim]

    feature_data_df = pd.DataFrame(feature_data)
    return feature_data_df

def predictions_from_idata(idata,
                           var_name):
    preds_helper = lambda ds: ds.to_dataframe()[var_name].value_counts(normalize=True).to_xarray()
    predictions = (
        idata.predictions[var_name]
            .stack(dims=['chain','draw'])
            .groupby('ball_ids')
            .apply(preds_helper)
    )
    predictions_argmax = predictions.argmax('index')
    predictions_max = predictions.max('index')
    predictions_df = pd.DataFrame({'batter_runs': predictions_argmax.values,
                                   'probability': predictions_max.values})
    return predictions, predictions_df


class BatterRunsModel:
    """Class to instantiate a ball level outcomes predictor for batter runs"""

    def __init__(self,
                 perfect_simulator: PerfectSimulator,
                 ):
        self.perfect_simulator = perfect_simulator
        self.idata_trained = load_idata_trained(
            "batter_runs_model/bayesian_inference/Indian Premier League_2009_and_selection_with_SR"
        )
        self.pymc_model = get_batter_runs_model(self.idata_trained)

    def prepare_for_prediction(self,
                               test_combined_df):
        self.pymc_model.set_dim('ball_ids',
                                test_combined_df.shape[0],
                                coord_values = np.arange(self.idata_trained.posterior.ball_ids[-1],
                                                         self.idata_trained.posterior.ball_ids[-1]+test_combined_df.shape[0]))
        with self.pymc_model:
            pm.set_data({
                "batter_featured_id_feature_data": test_combined_df['batter_featured_id'],
                "bowler_featured_id_feature_data": test_combined_df['bowler_featured_id'],
                "venue_feature_data": test_combined_df['venue'],
                "over_feature_data": test_combined_df['over'],
                "wickets_fallen_feature_data": test_combined_df['wickets_fallen'],
                "innings_strike_rate_feature_data": test_combined_df[['innings_strike_rate']].values,
                "batter_runs_outcomes_data": -1*np.ones_like(test_combined_df.venue.values)
            })

    def get_batter_runs_given_match_state(self,
                                          match_state_df):
        test_combined_df = prepare_match_state_df(match_state_df.reset_index(),
                                                  self.idata_trained)
        self.prepare_for_prediction(test_combined_df)
        with self.pymc_model:
            idata_predicted = pm.sample_posterior_predictive(
                self.idata_trained,
                predictions=True,
                extend_inferencedata=False,
                random_seed=RANDOM_SEED,
            )
        predictions_xarray,predictions_df = predictions_from_idata(idata_predicted,
                                                                   'batter_runs_outcome_by_ball_and_innings_rv')
        return predictions_df

