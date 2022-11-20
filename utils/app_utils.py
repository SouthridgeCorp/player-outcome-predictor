import arviz as az
import pandas as pd
import streamlit as st
from data_selection.data_selection import DataSelection
from historical_data.singleton import Helper
from historical_data.tournaments import Tournaments
from rewards_configuration.rewards_configuration import RewardsConfiguration
from utils.config_utils import create_utils_object, ConfigUtils
from simulators.predictive_simulator import PredictiveSimulator
from simulators.perfect_simulator import Granularity
from simulators.tournament_simulator import TournamentSimulator


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
    # This list governs the sequence in which metrics appear in the UI - changing this sequence will change the sequence
    # in the UI as well
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

    if 'TournamentSimulator' in st.session_state:
        del st.session_state['TournamentSimulator']


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


def get_tournament_simulator(force_initialise: bool) -> TournamentSimulator:
    """
    Helper instance to cache & acquire the tournament simulator.
    @param force_initialise: If true, forces a new instance to be initialised and replaced in the cache.
    @return An instance of TournamentSimulator which has already generated its scenarios
    """
    if ('TournamentSimulator' not in st.session_state) or force_initialise:
        tournament_simulator = TournamentSimulator(data_selection_instance(), rewards_instance(), create_utils_object())
        with st.spinner("Generating Scenarios"):
            tournament_simulator.generate_scenarios()
        if 'TournamentSimulator' in st.session_state:
            del st.session_state['TournamentSimulator']
        st.session_state['TournamentSimulator'] = tournament_simulator
    else:
        tournament_simulator = st.session_state['TournamentSimulator']

    return tournament_simulator


def has_tournament_simulator() -> bool:
    """
    Checks if the tournament simulator has already been generated & cached
    @return True if the simulator is available in the cache, False otherwise
    """
    return 'TournamentSimulator' in st.session_state


def get_granularity_list() -> list:
    """
    Gets the list of supported granularities
    """
    return ['None', Granularity.TOURNAMENT, Granularity.STAGE, Granularity.MATCH, Granularity.INNING]


def show_granularity_metrics(key_suffix: str, show_error_metrics: bool = True):
    """
    Streamlit helper function to show the granularity & metrics selection drop downs in the UI
    @param key_suffix: The name of the key to be tagged to the dropdowns
    @param show_error_metrics: Indicate if error metrics should be included in the metrics dropdown
    """
    granularity_select, metric_select = st.columns(2)

    with granularity_select:
        granularity_list = get_granularity_list()
        granularity = st.selectbox("Please select the granularity for reviewing Simulator stats",
                                   granularity_list, key=f"{key_suffix}_model_granularity")

    with metric_select:
        metrics, error_metrics = get_metrics_to_show()
        metrics_to_show = metrics
        if show_error_metrics:
            metrics_to_show = metrics + error_metrics
        metric = st.selectbox("Please select the metric to review", metrics_to_show,
                              key=f"{key_suffix}_model_metric")

    return granularity, metric, metrics, error_metrics


def show_stats(metric: str, summary_df: pd.DataFrame, indices: list) -> pd.DataFrame:
    """
    Calculate the stats for metric across all scenarios. Indices represents the index of the summary_df, and the
    dataframe returned by this function is indexed by the same set of indices.
    """
    summary_xarray = summary_df[metric].to_xarray()
    summary_xarray = summary_xarray.fillna(0.0)
    df = az.summary(summary_xarray)

    df = df.reset_index()
    start_len = len(metric) + 1

    # Parse the index value in df and extract out the actual index which can be used to interact with the source df.
    df['index'] = df['index'].str[start_len:-1]
    df = df.sort_values('mean', ascending=False)
    df[indices] = df['index'].str.split(", ", expand=True)
    for index in indices:
        df[index].str.strip()
        # TODO: Find a way to avoid this hack (though it is not an expensive hack)
        if (index == 'match_key') or (index == 'inning'):
            df[index] = df[index].astype(int)
    df.set_index(indices, inplace=True, verify_integrity=True)
    df.rename(columns={'mean': metric}, inplace=True)
    return df


def show_top_X(metric: str, df: pd.DataFrame, indices: list, number_of_players: int, reference_df: pd.DataFrame=None):
    """
    Show the top X rows sorted by the metric - streamlit helper function which also displays the tables in the UI
    @param metric: the metric to summarise
    @param df: the dataframe containing all scenarios of the metric to summarise
    @param indices: the indices to set for the stats returned
    @param number_of_players: the number of players to summarise
    @param reference_df: the reference dataframe to lookup for the name of the players
    """
    metric_stats_df = show_stats(metric, df, indices)
    if reference_df is not None:
        metric_stats_df = pd.merge(reference_df[['name']], metric_stats_df, left_index=True, right_index=True)

    metric_stats_df = metric_stats_df.sort_values(metric, ascending=False)
    st.dataframe(metric_stats_df[['name', metric]].drop_duplicates().head(number_of_players),
                 use_container_width=True)


def write_top_X_to_st(max_players, df: pd.DataFrame, indices: list, reference_df=None, column_suffix=""):
    """
    Helper streamlit function to prepare for & show the top X players
    """
    # Show the top players
    number_of_players = st.slider("Select the number of top players to show:", min_value=0,
                                  max_value=max_players, value=30)

    top_players_column, top_batters_column, top_bowlers_column = st.columns(3)

    with top_players_column:
        st.subheader(f'Top {number_of_players} Players')
        show_top_X(f'total_rewards{column_suffix}', df, indices,
                   number_of_players=number_of_players, reference_df=reference_df)

    with top_bowlers_column:
        st.subheader(f'Top {number_of_players} Bowlers')
        show_top_X(f'bowling_rewards{column_suffix}', df, indices,
                   number_of_players=number_of_players, reference_df=reference_df)

    with top_batters_column:
        st.subheader(f'Top {number_of_players} Batters')
        show_top_X(f'batting_rewards{column_suffix}', df, indices,
                   number_of_players=number_of_players, reference_df=reference_df)
