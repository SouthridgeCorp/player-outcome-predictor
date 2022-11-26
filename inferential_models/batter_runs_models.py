import numpy as np
import pandas as pd
import pymc as pm
from pymc.util import dataset_to_point_list
from sklearn.preprocessing import OneHotEncoder
from sklearn.ensemble import RandomForestClassifier
import aesara.tensor as at
from simulators.perfect_simulator import PerfectSimulator
import pickle
import logging
from sklearn.metrics import classification_report, confusion_matrix
import os

logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

RANDOM_SEED = 8265

def load_idata_trained(model_path):
    """
    Loads a trained Bayesian Inference model from model_path and returns the trace
    :param model_path: File with the stored model
    :return: InferenceData instance which is the trace
    """
    with open(model_path, 'rb') as buff:
        data = pickle.load(buff)
    idata = data['trace']
    return idata

def load_random_forest_classifier(model_path):
    """
    Loads a trained Random Forest classifier model from model_path and returns the trace
    :param model_path: File with the stored model
    :return: tuple containing the classifier instance and the one-hot encoders for the model
    """
    with open(model_path, 'rb') as buff:
        payload = pickle.load(buff)
    return payload['classifier'], payload['one_hot_encoders']

def save_idata_trained(idata_trained,
                       model_path):
    """Saves a trained bayesian inf model (idata_trained, an InferenceData instance) to model_path"""
    with open(model_path, 'wb') as buff:
        pickle.dump({'trace': idata_trained}, buff)

def save_random_forest_classifier(clf,
                                  one_hot_encoders,
                                  model_path):
    """Saves a trained random forest model (clf) and its one-hot encoders to model_path"""
    with open(model_path, 'wb') as buff:
        payload = {
            'classifier': clf,
            'one_hot_encoders': one_hot_encoders
        }
        pickle.dump(payload, buff)

def get_cr_and_cm(true,pred):
    """Returns the classification report and confusion matrix comparing true with pred"""
    cr = classification_report(true,pred)
    cm = confusion_matrix(true,pred)
    return cr,pd.DataFrame(cm)

def build_categoricals_for_column(df,column):
    """Returns the categories found in d[column] for converting pd.Categorical variables in other dataframes"""
    categorical = pd.Categorical(df[column])
    return categorical.categories

def build_xarray(feature_dict,
                 outcome_dict):
    """Stack feature_dict and outcome_dict to produce a combined feature + outcome array.
    Returns this in dataframe and xarray formats"""
    feature_df = pd.DataFrame(feature_dict)
    #feature_df.index = index_df.index
    outcome_df = pd.DataFrame(outcome_dict)
    #outcome_df.index = index_df.index
    combined_df = pd.merge(outcome_df,
                           feature_df,
                           left_index = True,
                           right_index = True)
    return combined_df, combined_df.to_xarray()

def prepare_training_data_for_bayesian_inference(match_state_df,
                                                 bowling_outcomes_df):
    """
    Prepare all the artefacts required to set up a pymc model for training
    :param match_state_df: DataFrame representing state of the match before a ball is bowled
    :param bowling_outcomes_df: DataFrame representing the outcomes of the ball
    :return:
        COORDS: Dictionary that catalogs all the dimensions and co-ordinates for the PyMC model
        train_combined_df: Combined dataframe that includes match state and outcome data
        train_combined_xarray: Combined xArray that includes match state and outcome data
    """
    temp_match_state_df = match_state_df.reset_index()
    COORDS = {}
    train_feature_data = {}
    for dim in ['batter',
                'bowler',
                'venue',
                'wickets_fallen',
                'over',
                'match_key',
                'inning',
                'ball']:
        categories = build_categoricals_for_column(temp_match_state_df,
                                                   dim)
        COORDS[dim] = categories
        train_feature_data[dim] = get_categorical_column_index_for_df(temp_match_state_df,
                                                                      categories,
                                                                      dim)
    for feature in [innings_strike_rate]:
        add_column_to_df(temp_match_state_df,
                         feature)

    for feature in ['innings_strike_rate']:
        train_feature_data[feature] = temp_match_state_df[feature].values

    train_outcome_data = {}

    for dim in ['batter_runs']:
        categories = build_categoricals_for_column(bowling_outcomes_df,
                                                   dim)
        COORDS[dim] = categories
        train_outcome_data[dim] = get_categorical_column_index_for_df(bowling_outcomes_df,
                                                                      categories,
                                                                      dim)
    train_combined_df, train_combined_xarray = build_xarray(train_feature_data,
                                                            train_outcome_data,
                                                            match_state_df)
    return COORDS,train_combined_df,train_combined_xarray

def get_batter_runs_bi_model_from_perfect_simulator(perfect_simulator):
    """
    Instantinate a pymc model from a perfect simulator instance
    :param perfect_simulator: Instance of perfect simulator that represents the test and train data for the model
    :return:
        batter_runs_model: Untrained PyMC model (network only) for inferring batter_runs from match state
    """
    train_match_state_df,train_bowling_outcomes_df,_ = perfect_simulator.get_match_state_by_balls_for_training()
    COORDS, train_combined_df,train_combined_xarray = prepare_training_data_for_bayesian_inference(train_match_state_df,
                                                                                                   train_bowling_outcomes_df)
    with pm.Model(coords=COORDS) as batter_runs_model:
        batter_runs_model.add_coord('ball_ids',
                                    values=np.arange(train_combined_df.shape[0]),
                                    mutable=True)
        batter_runs_outcomes_data = pm.MutableData("batter_runs_outcomes_data",
                                                   train_combined_df['batter_runs'],
                                                   dims='ball_ids')
        batter_featured_id_feature_data = pm.MutableData("batter_featured_id_feature_data",
                                                         train_combined_df['batter'],
                                                         dims='ball_ids')
        bowler_featured_id_feature_data = pm.MutableData("bowler_featured_id_feature_data",
                                                         train_combined_df['bowler'],
                                                         dims='ball_ids')
        venue_feature_data = pm.MutableData("venue_feature_data",
                                            train_combined_df['venue'],
                                            dims='ball_ids')
        over_feature_data = pm.MutableData("over_feature_data",
                                           train_combined_df['over'],
                                           dims='ball_ids')
        inning_feature_data = pm.MutableData("inning_feature_data",
                                             train_combined_df['inning'],
                                             dims='ball_ids')
    with batter_runs_model:
        wickets_fallen_feature_data = pm.MutableData("wickets_fallen_feature_data",
                                                     train_combined_df['wickets_fallen'],
                                                     dims='ball_ids')
        innings_strike_rate_feature_data = pm.MutableData("innings_strike_rate_feature_data",
                                                          train_combined_df[['innings_strike_rate']].values)
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
                                                        dims=('batter',
                                                              'batter_runs'))
        batter_runs_outcome_alpha_by_bowler = pm.Normal('batter_runs_outcome_alpha_by_bowler',
                                                        mu=0,
                                                        sigma=3.0,
                                                        dims=('bowler',
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
        batter_runs_outcome_mu = pm.Deterministic('mu_batter_runs_outcome_rv',
                                                  batter_runs_outcome_alpha +
                                                  batter_runs_outcome_alpha_by_batter[
                                                      batter_featured_id_feature_data] +
                                                  batter_runs_outcome_alpha_by_bowler[
                                                      bowler_featured_id_feature_data] +
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
    return batter_runs_model

def get_batter_runs_rf_model_from_perfect_simulator(perfect_simulator):
    """
    Instantiate inputs for a random forest model from a perfect simulator instance
    :param perfect_simulator: Instance of perfect simulator that represents the test and train data for the model
    :return:
        train_ohe_features: dictionary mapping feature names to feature vectors
        train_ohe_feature_array: numpy array with all features include OHE features
        one_hot_encoders: dict mapping feature names to OHEs that can be used to encode other feature vectors
        targets: batter runs outcomes from perfect simulator
    """
    train_match_state_df,train_bowling_outcomes_df,_ = perfect_simulator.get_match_state_by_balls_for_training()
    train_match_state_df = train_match_state_df.reset_index()
    one_hot_encoders = {}
    train_ohe_features = {}
    for feature in ['batter', 'bowler', 'venue', 'over', 'inning', 'wickets_fallen']:
        ohe = OneHotEncoder(sparse=False,
                            handle_unknown='infrequent_if_exist')
        train_features = ohe.fit_transform(train_match_state_df[[feature]])
        one_hot_encoders[feature] = ohe
        train_ohe_features[feature] = train_features

    for feature in [innings_strike_rate]:
        add_column_to_df(train_match_state_df,
                         feature)

    for feature in ['innings_strike_rate']:
        train_ohe_features[feature] = train_match_state_df[[feature]].values

    train_ohe_feature_array = np.hstack(
        [v[1] for v in train_ohe_features.items()]
    )

    targets = train_bowling_outcomes_df['batter_runs']
    return train_ohe_features, train_ohe_feature_array, one_hot_encoders, targets

def get_batter_runs_model_from_idata(idata_trained):
    """
    Instantinate a trained pymc model from an inference data object that reprsents its trace
    :param idata_trained: InferenceData instance that contains the trace for the model
    :return:
        batter_runs_model: Trained PyMC model for inferring batter_runs from match state
    """
    logger.info(f"Preparing bayesian inference model trained on {idata_trained.constant_data.ball_ids.shape}")
    COORDS = {
        'batter_runs': idata_trained.posterior.batter_runs.values,
        'batter': idata_trained.posterior.batter.values,
        'bowler': idata_trained.posterior.bowler.values,
        'over': idata_trained.posterior.over.values,
        'venue': idata_trained.posterior.venue.values,
        'wickets_fallen': idata_trained.posterior.wickets_fallen.values
    }
    with pm.Model(coords=COORDS) as model:
        model.add_coord('ball_ids',
                        values=idata_trained.constant_data.ball_ids.values,
                        mutable=True)
        batter_runs_outcomes_data = pm.MutableData("batter_runs_outcomes_data",
                                                   idata_trained.constant_data['batter_runs_outcomes_data'],
                                                   dims='ball_ids')
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
                                                        dims=('batter',
                                                              'batter_runs'))
        batter_runs_outcome_alpha_by_bowler = pm.Normal('batter_runs_outcome_alpha_by_bowler',
                                                        mu=0,
                                                        sigma=3.0,
                                                        dims=('bowler',
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
    """Returns the categorical index for df[column] based on categories"""
    transformed_column_name = column.split('_')[0] if 'featured_id' in column else column
    if transformed_column_name == 'wickets_fallen' and 'wickets_fallen' not in df:
        transformed_column_name = 'previous_number_of_wickets'
    idx = pd.Categorical(df[transformed_column_name],
                         categories).codes
    return idx

def innings_strike_rate(df):
    """Add the innings_strike_rate feature to the input df"""
    if 'previous_total' in df.columns and 'total_balls_bowled' in df.columns:
        df['innings_strike_rate'] = df['previous_total'] / df['total_balls_bowled']
    else:
        df['innings_strike_rate'] = df['previous_total'] / (df['over']*6 + df['ball'])
    df['innings_strike_rate'].fillna(0, inplace=True)
    df['innings_strike_rate'].replace([np.inf, -np.inf], 0, inplace=True)


def add_column_to_df(df,
                     column_name):
    """Pass df to the column_name function and have it operate on the whole df. Usually to add a column
    to it"""
    column_name(df)

def prepare_match_state_df_for_bi(match_state_df,
                                  idata_trained):
    """
    Restructure a match_state_df generated by a simulator instance into a feature dataframe that will be understood
    by a pymc model that uses idata_trained.posterior as its trace.
    :param match_state_df: DataFrame representing match state before a ball is bowled
    :param idata_trained: InferenceData instance representing the trained model
    :return:
        feature_data_df: DataFrame with all features needed by idata_trained, properly categorized.
    """
    feature_data = {}
    for dim in ['batter',
                'bowler',
                'venue',
                'wickets_fallen',
                'over']:
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


def prepare_match_state_df_for_rf(match_state_df,
                                  one_hot_encoders):
    """
    Restructure a match_state_df generated by a simulator instance into a feature dataframe that will be understood
    by a random forest model that uses one_hot_encoders to transform features.
    :param match_state_df: DataFrame representing match state before a ball is bowled
    :param one_hot_encoders: Dict mapping features to one hot encoders
    :return:
        feature_array: Array with all features for RF inference
        feature_data: Dict mapping feature names to feature vectors for RF inference
    """
    dim_transform = {
        'wickets_fallen': 'previous_number_of_wickets'
    }

    feature_data = {}
    for dim in ['batter',
                'bowler',
                'venue',
                'wickets_fallen',
                'over',
                'inning']:
        ohe = one_hot_encoders[dim]
        if dim not in match_state_df.columns:
            transformed_dim = dim_transform[dim]
        else:
            transformed_dim = dim
        feature_data[dim] = ohe.transform(match_state_df[[transformed_dim]])

    for column in [innings_strike_rate]:
        add_column_to_df(match_state_df,
                         column)

    for dim in ['innings_strike_rate']:
        feature_data[dim] = match_state_df[[dim]]

    feature_array = np.hstack(
        [v[1] for v in feature_data.items()]
    )
    return feature_array, feature_data

def predictions_from_idata(idata,
                           var_name):
    """
    Calculate the percentage of scenarios of var_name for each category. Return this in xarray and
    dataframe formats
    :param idata: Inference data object containing scenarios for categorical variable var_name
    :param var_name: Categorical variable whose frequency we want to count across scenarios
    :return:
        predictions_df: DataFrame containing predictions for the var name along with the probability
        prediction: Inference data version of the same
    """
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
                 model_directory_path: str,
                 model_type: str):
        self.perfect_simulator = perfect_simulator
        self.model_directory_path = model_directory_path
        self.model_type = model_type
        self.model_path = self.construct_model_path()

    def construct_model_path(self):
        try:
            test_tournament = self.perfect_simulator.data_selection.historical_data_helper.tournaments.testing_selected_tournament
            test_season = self.perfect_simulator.data_selection.historical_data_helper.tournaments.testing_selected_season
            (train_start_date, train_end_date) = self.perfect_simulator.data_selection.historical_data_helper.tournaments.get_training_start_end_dates()
            data_selection_type = self.perfect_simulator.data_selection.get_selection_type()
            model_dir =  f"{self.model_directory_path}/" \
                         f"{self.model_type}/"
            if not os.path.isdir(model_dir):
                os.makedirs(model_dir)
            model_path = f"{model_dir}/" \
                         f"{test_tournament}~" \
                         f"{test_season}~" \
                         f"{train_start_date}~" \
                         f"{train_end_date}~" \
                         f"{data_selection_type}.pkl"
        except Exception as e:
            model_path = f"{self.model_directory_path}/" \
                         f"{self.model_type}/" \
                         'Indian Premier League_2009_or_selection_with_SR.pkl'
        logger.info(f"Instantiated with model_path = {model_path}")
        return model_path

    def initiate_model(self,session_type='training'):
        logger.info(f"Initating {self.model_type} for {session_type}")
        if self.model_type == 'bayesian_inference':
            self.initiate_bayesian_inference_model(session_type)
        if self.model_type == 'random_forest':
            self.initiate_random_forest_model(session_type)

    def initiate_bayesian_inference_model(self,session_type='training'):
        if session_type == 'training':
            self.training_status = False
            self.pymc_model = get_batter_runs_bi_model_from_perfect_simulator(self.perfect_simulator)
        if session_type == 'testing':
            self.idata_trained = load_idata_trained(
                self.model_path
            )
            self.posterior_point_list = dataset_to_point_list(self.idata_trained.posterior)
            self.pymc_model = get_batter_runs_model_from_idata(self.idata_trained)
            self.training_status = True

    def initiate_random_forest_model(self,session_type='training'):
        if session_type == 'training':
            self.training_status = False
            (self.train_ohe_features,
             self.train_ohe_feature_array,
             self.one_hot_encoders,
             self.targets)  = get_batter_runs_rf_model_from_perfect_simulator(self.perfect_simulator)
            logger.info(f"Initated random forest model with training shape = {self.train_ohe_feature_array.shape}")
        if session_type == 'testing':
            self.random_forest_classifier,self.one_hot_encoders = load_random_forest_classifier(
                self.model_path
            )
            self.training_status = True
            logger.info(f"Initated random forest model with for testing using {self.model_path}")

    def run_training(self):
        if self.model_type == 'bayesian_inference':
            self.train_bayesian_inference()
        if self.model_type == 'random_forest':
            self.train_random_forest()

    def train_bayesian_inference(self):
        with self.pymc_model:
            self.idata_trained = pm.sample(random_seed=RANDOM_SEED)
        self.posterior_point_list = dataset_to_point_list(self.idata_trained.posterior)
        self.training_status = True
        save_idata_trained(self.idata_trained,
                           self.model_path)

    def train_random_forest(self):
        clf = RandomForestClassifier()
        clf.fit(self.train_ohe_feature_array,
                self.targets)
        self.random_forest_classifier = clf
        self.training_status = True
        save_random_forest_classifier(self.random_forest_classifier,
                                      self.one_hot_encoders,
                                      self.model_path)

    def run_testing(self):
        if self.model_type == 'bayesian_inference':
            testing_stats = self.test_bayesian_inference()
        if self.model_type == 'random_forest':
            testing_stats = self.test_random_forest()
        return testing_stats

    def test_bayesian_inference(self):
        test_match_state_df = self.perfect_simulator.get_match_state_by_ball_and_innings(True)
        test_bowling_outcomes_df = self.perfect_simulator.get_bowling_outcomes_by_ball_and_innings(True)
        predictions_df = self.run_bayesian_inference_prediction(test_match_state_df)
        cr,cm = get_cr_and_cm(test_bowling_outcomes_df['batter_runs'],
                              predictions_df['batter_runs'])
        ret =  {
            "classification_report": cr,
            "confusion_matrix": cm
        }
        return ret
    def test_random_forest(self):
        test_match_state_df = self.perfect_simulator.get_match_state_by_ball_and_innings(True)
        test_bowling_outcomes_df = self.perfect_simulator.get_bowling_outcomes_by_ball_and_innings(True)
        predictions_df = self.run_random_forest_prediction(test_match_state_df)
        cr,cm = get_cr_and_cm(test_bowling_outcomes_df['batter_runs'],
                              predictions_df['batter_runs'])
        ret =  {
            "classification_report": cr,
            "confusion_matrix": cm
        }
        return ret

    def prepare_for_prediction(self,
                               test_combined_df):
        self.pymc_model.set_dim('ball_ids',
                                test_combined_df.shape[0],
                                coord_values = np.arange(self.idata_trained.posterior.ball_ids[-1],
                                                         self.idata_trained.posterior.ball_ids[-1]+test_combined_df.shape[0]))
        with self.pymc_model:
            pm.set_data({
                "batter_featured_id_feature_data": test_combined_df['batter'],
                "bowler_featured_id_feature_data": test_combined_df['bowler'],
                "venue_feature_data": test_combined_df['venue'],
                "over_feature_data": test_combined_df['over'],
                "wickets_fallen_feature_data": test_combined_df['wickets_fallen'],
                "innings_strike_rate_feature_data": test_combined_df[['innings_strike_rate']].values,
                "batter_runs_outcomes_data": -1*np.ones_like(test_combined_df.venue.values)
            })

    def run_bayesian_inference_prediction(self,
                                          match_state_df,
                                          sample_once = True):
        test_combined_df = prepare_match_state_df_for_bi(match_state_df.reset_index(),
                                                         self.idata_trained)
        logger.info(f'Received match state with {test_combined_df.shape[0]} balls for inference')
        self.prepare_for_prediction(test_combined_df)
        logger.info(f'Prepared for inference for {test_combined_df.shape[0]} balls')
        with self.pymc_model:
            if sample_once:
                idata_predicted = pm.sample_posterior_predictive(
                    self.posterior_point_list,
                    samples=1,
                    keep_size=False,
                    predictions=True,
                    extend_inferencedata=False,
                    random_seed=RANDOM_SEED,
                    return_inferencedata=False
                )
            else:
                idata_predicted = pm.sample_posterior_predictive(
                    self.posterior_point_list,
                    keep_size=False,
                    predictions=True,
                    extend_inferencedata=False,
                    random_seed=RANDOM_SEED
                )
        logger.info(f'Formatting inference for {test_combined_df.shape[0]} balls')
        if sample_once:
            predictions_df = pd.DataFrame({'batter_runs':idata_predicted['batter_runs_outcome_by_ball_and_innings_rv'][0]})
        else:
            try:
                predictions_xarray,predictions_df = predictions_from_idata(idata_predicted,
                                                                           'batter_runs_outcome_by_ball_and_innings_rv')
            except Exception as e:
                logger.error(f"Error while formatting inference for {test_combined_df.shape[0]} balls: {e}")
                predictions_df = pd.DataFrame()
        logger.info(f'Inferred batter runs for {predictions_df.shape[0]} balls')
        return predictions_df

    def run_random_forest_prediction(self,
                                     match_state_df):
        rf_feature_array, rf_feature_data = prepare_match_state_df_for_rf(match_state_df.reset_index(),
                                                                          self.one_hot_encoders)
        logger.info(f'Received match state with {match_state_df.shape[0]} balls for inference')
        predictions_array = self.random_forest_classifier.predict(rf_feature_array)
        predictions_df = pd.DataFrame({'batter_runs': predictions_array})
        logger.info(f'Inferred batter runs for {predictions_df.shape[0]} balls')
        return predictions_df

    def get_batter_runs_given_match_state(self,
                                          match_state_df):
        """
        Returns the models opinion of batter runs outcomes for the provided match_state_df
        :param match_state_df: DataFrame representing match state before a ball is bowled
        :return:
            predictions_df: DataFrame with the model's predictions.
        """
        if self.model_type == 'bayesian_inference':
            predictions_df = self.run_bayesian_inference_prediction(match_state_df)
        if self.model_type == 'random_forest':
            predictions_df = self.run_random_forest_prediction(match_state_df)

        return predictions_df

