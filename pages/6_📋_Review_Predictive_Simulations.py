import streamlit as st
import utils.page_utils as page_utils
from utils.config_utils import create_utils_object
from utils.app_utils import data_selection_instance, rewards_instance, data_selection_summary, get_metrics_to_show, \
    get_predictive_simulator
from simulators.predictive_simulator import PredictiveSimulator
from simulators.perfect_simulator import PerfectSimulator, Granularity
from data_selection.data_selection import DataSelection
import pandas as pd
import arviz as az
import logging


def show_stats(metric, summary_df, indices):
    summary_xarray = summary_df[metric].to_xarray()
    df = az.summary(summary_xarray)
    df = df.reset_index()
    start_len = len(metric) + 1

    df['index'] = df['index'].str[start_len:-1]
    df = df.sort_values('mean', ascending=False)
    df[indices] = df['index'].str.split(", ", expand=True)
    for index in indices:
        df[index].str.strip()
        if (index == 'match_key') or (index == 'inning'):
            df[index] = df[index].astype(int)
    df.set_index(indices, inplace=True, verify_integrity=True)
    df.rename(columns={'mean': metric}, inplace=True)
    return df


def show_top_X(metric, total_errors_df, total_errors_index, reference_df, number_of_players):
    metric_stats_df = show_stats(metric, total_errors_df, total_errors_index)
    metric_stats_df = pd.merge(reference_df[['name']],
                               metric_stats_df, left_index=True, right_index=True)
    metric_stats_df = metric_stats_df.sort_values(metric, ascending=False)
    st.dataframe(metric_stats_df[['name', metric]].head(number_of_players),
                 use_container_width=True)


def show_summary(title, panel, summary_df, data_selection: DataSelection):
    """
    Calculate the summary stats for the supplied summary_df, and write them out into the st widget provided. This
    function also sorts the summary by mean and replaces player key by player name for display.
    """
    with panel:
        st.write(f"{title}")
        summary_xarray = summary_df.to_xarray()
        df = az.summary(summary_xarray)
        df = df.reset_index()
        start_len = len(title) + 1

        df['index'] = df['index'].str[start_len:-1].str.split(',').str[0]
        df = data_selection.merge_with_players(df, 'index')
        df = df.sort_values('mean', ascending=False)
        st.write(df[['name', 'mean', 'sd', 'hdi_3%', 'hdi_97%']])


@st.cache
def calculate_error_metrics(number_of_scenarios, granularity, rewards, perfect_simulator):

    predictive_simulator = get_predictive_simulator(rewards, number_of_scenarios)

    total_errors_df = pd.DataFrame()
    perfect_df = perfect_simulator.get_simulation_evaluation_metrics_by_granularity(True, granularity)
    for scenario in range(0, number_of_scenarios):
        comparison_df = predictive_simulator.perfect_simulators[scenario]. \
            get_simulation_evaluation_metrics_by_granularity(True, granularity)
        errors_df = perfect_simulator.get_error_measures(True, comparison_df, granularity, perfect_df)

        # Add scenario numbers and collate all the error metrics into one big error df for stats calculations
        errors_df['scenario_number'] = scenario
        total_errors_df = pd.concat([total_errors_df, errors_df])

    return total_errors_df



def app():
    page_utils.setup_page(" Review Predictive Simulation ")
    enable_debug = st.checkbox("Click here to enable detailed logging", value=True)
    if enable_debug:
        logging.basicConfig()
        logging.getLogger().setLevel(logging.DEBUG)

    data_selection = data_selection_instance()
    tournaments = data_selection.get_helper().tournaments
    rewards = rewards_instance()
    # Show a summary of selected training & testing windows
    data_selection_summary(tournaments)
    config_utils = create_utils_object()
    number_of_scenarios = config_utils.get_predictive_simulator_info()

    st.write(f"Number of scenarios: {number_of_scenarios}")

    granularity_select, metric_select = st.columns(2)

    with granularity_select:
        granularity_list = ['None', Granularity.TOURNAMENT, Granularity.STAGE, Granularity.MATCH, Granularity.INNING]
        granularity = st.selectbox("Please select the granularity for reviewing Simulator stats",
                                   granularity_list, key="predictive_model_granularity")

    with metric_select:
        metric = st.selectbox("Please select the metric to review", get_metrics_to_show(),
                              key="predictive_model_metric")

    if granularity == 'None':
        st.write("Please select a valid Granularity")
    else:
        perfect_simulator = PerfectSimulator(data_selection, rewards)

        # with st.spinner("Generating Scenarios"):
        #   predictive_simulator = PredictiveSimulator(data_selection_instance(), rewards, number_of_scenarios)
        #  matches_df, innings_df = get_predictive_scenarios(predictive_simulator, rewards, number_of_scenarios)

        # with st.spinner('Calculating Error Measures'):
        total_errors_df = calculate_error_metrics(number_of_scenarios, granularity, rewards, perfect_simulator)

        total_errors_index = total_errors_df.index.names
        reference_df = total_errors_df.reset_index().query('scenario_number == 0')
        reference_df.set_index(total_errors_index, inplace=True, verify_integrity=True)

        total_errors_df = total_errors_df.reset_index()

        # Remove non-numeric values
        total_errors_df = total_errors_df.drop('name', axis=1)

        # Set up the dataframe for statistical calculations
        total_errors_df['chain'] = 0
        total_errors_df.rename(columns={"scenario_number": "draw"}, inplace=True)
        total_errors_df.set_index(['chain', 'draw'] + total_errors_index, inplace=True, verify_integrity=True)

        if 'absolute' not in metric:
            metric_stats_df = show_stats(f'{metric}_received', total_errors_df, total_errors_index)
            metric_stats_df = pd.merge(reference_df[['name', f'{metric}_expected']],
                                       metric_stats_df, left_index=True, right_index=True)
            metric_stats_df = metric_stats_df.sort_values(f'{metric}_received', ascending=False)
            st.dataframe(metric_stats_df[['name',
                                          f'{metric}_expected', f'{metric}_received', 'sd', 'hdi_3%', 'hdi_97%']],
                         use_container_width=True)
        else:
            metric_stats_df = show_stats(metric, total_errors_df, total_errors_index)
            metric_stats_df = pd.merge(reference_df[['name']],
                                       metric_stats_df, left_index=True, right_index=True)
            metric_stats_df = metric_stats_df.sort_values(metric, ascending=False)
            st.dataframe(metric_stats_df[['name', metric, 'sd', 'hdi_3%', 'hdi_97%']],
                         use_container_width=True)

        number_of_players = st.slider("Select the number of top players to show:", min_value=0,
                                      max_value=len(metric_stats_df.index), value=30)

        top_players_column, top_batters_column, top_bowlers_column = st.columns(3)

        with top_players_column:
            st.subheader(f'Top {number_of_players} Players')
            show_top_X('total_rewards_received', total_errors_df, total_errors_index, reference_df, number_of_players)

        with top_bowlers_column:
            st.subheader(f'Top {number_of_players} Bowlers')
            show_top_X('bowling_rewards_received', total_errors_df, total_errors_index, reference_df, number_of_players)

        with top_batters_column:
            st.subheader(f'Top {number_of_players} Batters')
            show_top_X('batting_rewards_received', total_errors_df, total_errors_index, reference_df, number_of_players)


app()
