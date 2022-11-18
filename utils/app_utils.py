import streamlit as st
from data_selection.data_selection import DataSelection
from historical_data.singleton import Helper
from historical_data.tournaments import Tournaments
from rewards_configuration.rewards_configuration import RewardsConfiguration
from utils.config_utils import create_utils_object, ConfigUtils
from simulators.predictive_simulator import PredictiveSimulator
from simulators.perfect_simulator import Granularity


def data_selection_instance():
    """
    Helper function to get a singleton instance of the data_selection config. To only be used within streamlit
    :return: An instance of DataSelection
    """
    if 'DataSelection' not in st.session_state:
        config_utils = create_utils_object()
        # get the helper from the singleton instance
        helper = get_helper(config_utils)
        # get a data selection instance from the singleton
        st.session_state['DataSelection'] = DataSelection(helper)

    return st.session_state['DataSelection']


def rewards_instance() -> RewardsConfiguration:
    """
    Helper function to get a singleton instance of the rewards config. To only be used within streamlit
    :return: An instance of RewardsConfiguration
    """
    if 'RewardsConfig' not in st.session_state:
        config_utils = create_utils_object()
        st.session_state['RewardsConfig'] = RewardsConfiguration(config_utils)

    return st.session_state['RewardsConfig']


def get_helper(config_utils: ConfigUtils) -> Helper:
    """
    This function returns a singleton instance of the Helper (by utilising the streamlit session state).
    Note: this function only works in the streamlit context
    :param config_utils: The config_utils object used to configure the helper
    :return: A Helper class
    """
    if 'MatchUtilsHelper' not in st.session_state:
        st.session_state['MatchUtilsHelper'] = Helper(config_utils)
    return st.session_state['MatchUtilsHelper']


def data_selection_summary(tournaments: Tournaments):
    """
    Builds out the summary of data selection fields for displaying in streamlit. Can be used to summarise the current
    state of data selection on any streamlit page.
    """
    selected_tournaments, training, testing = st.columns(3)

    with selected_tournaments:
        st.subheader("Selected Tournaments:")
        st.write(tournaments.get_selected_tournament_names())

    with training:
        st.subheader("Training Details:")
        training_start_date, training_end_date = tournaments.get_start_end_dates(False)
        st.write(f"Start Date: {training_start_date}")
        st.write(f"End Date: {training_end_date}")

    with testing:
        st.subheader("Testing Details:")
        testing_start_date, testing_end_date = tournaments.get_start_end_dates(True)
        st.write(f"Start Date: {testing_start_date}")
        st.write(f"End Date: {testing_end_date}")


def get_metrics_to_show() -> (list, list):
    """
    Returns a list of metrics to display and the corresponding error measures for the metrics. Used by the simulators
    UI pages usually.
    """
    metric_list = ['total_rewards', 'bowling_rewards', 'batting_rewards', 'fielding_rewards']
    error_metrics = []
    for item in metric_list:
        error_metrics.append(f"{item}_absolute_error")
        error_metrics.append(f"{item}_absolute_percentage_error")

    return metric_list, error_metrics


def reset_session_states():
    """
    To be called whenever a major change requires a session state reset. Keep updating this function as and when new
    session objects are added.
    """
    if 'PredictiveSimulator' in st.session_state:
        del st.session_state['PredictiveSimulator']


def get_predictive_simulator(rewards, number_of_scenarios) -> PredictiveSimulator:
    """
    Helper instance to cache & acquire the predictive simulator.
    """
    if 'PredictiveSimulator' not in st.session_state:
        predictive_simulator = PredictiveSimulator(data_selection_instance(), rewards, number_of_scenarios)
        predictive_simulator.generate_scenario()
        st.session_state['PredictiveSimulator'] = predictive_simulator
    else:
        predictive_simulator = st.session_state['PredictiveSimulator']

    return predictive_simulator


def show_granularity_metrics(key_suffix):
    granularity_select, metric_select = st.columns(2)

    with granularity_select:
        granularity_list = ['None', Granularity.TOURNAMENT, Granularity.STAGE, Granularity.MATCH, Granularity.INNING]
        granularity = st.selectbox("Please select the granularity for reviewing Simulator stats",
                                   granularity_list, key=f"{key_suffix}_model_granularity")

    with metric_select:
        metrics, error_metrics = get_metrics_to_show()
        metrics_to_show = metrics + error_metrics
        metric = st.selectbox("Please select the metric to review", metrics_to_show,
                              key=f"{key_suffix}_model_metric")

    return granularity, metric, metrics, error_metrics
