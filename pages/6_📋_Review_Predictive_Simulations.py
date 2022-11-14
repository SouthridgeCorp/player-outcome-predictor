import streamlit as st
import utils.page_utils as page_utils
from utils.config_utils import create_utils_object
from utils.app_utils import data_selection_instance, rewards_instance, data_selection_summary
from simulators.predictive_simulator import PredictiveSimulator
from simulators.perfect_simulator import PerfectSimulator, Granularity
from data_selection.data_selection import DataSelection
import pandas as pd
import arviz as az


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
        df['index'] = df['index'].str[start_len:-1]
        df = data_selection.merge_with_players(df, 'index')
        df = df.sort_values('mean', ascending=False)
        st.write(df[['name', 'mean', 'sd', 'hdi_3%', 'hdi_97%']])


def app():
    page_utils.setup_page(" Review Predictive Simulation ")

    data_selection = data_selection_instance()
    tournaments = data_selection.get_helper().tournaments
    rewards = rewards_instance()
    # Show a summary of selected training & testing windows
    data_selection_summary(tournaments)
    config_utils = create_utils_object()
    number_of_scenarios = config_utils.get_predictive_simulator_info()
    predictive_simulator = PredictiveSimulator(data_selection, rewards, number_of_scenarios)

    st.write(f"Number of scenarios: {number_of_scenarios}")

    # TODO: Replace by a granularity drop-down eventually
    granularity = Granularity.TOURNAMENT
    st.write(f"Granularity: {granularity}")

    if granularity == 'None':
        st.write("Please select a valid Granularity")
    else:

        perfect_simulator = PerfectSimulator(data_selection, rewards)

        with st.spinner("Generating Scenarios"):
            predictive_simulator.generate_scenario()

        with st.spinner('Calculating Error Measures'):
            perfect_df = perfect_simulator.get_simulation_evaluation_metrics_by_granularity(True, granularity)
            total_errors_df = pd.DataFrame()
            for scenario in range(0, number_of_scenarios):
                comparison_df = predictive_simulator.perfect_simulators[scenario]. \
                    get_simulation_evaluation_metrics_by_granularity(True, granularity)
                errors_df = perfect_simulator.get_error_measures(True, comparison_df, granularity, perfect_df)

                # Add scenario numbers and collate all the error metrics into one big error df for stats calculations
                errors_df['scenario_number'] = scenario
                total_errors_df = pd.concat([total_errors_df, errors_df])

        total_errors_df = total_errors_df.reset_index()

        # Remove non-numeric values
        total_errors_df = total_errors_df.drop('tournament_key', axis=1)

        # Set up the dataframe for statistical calculations
        total_errors_df['chain'] = 0
        total_errors_df.rename(columns={"scenario_number": "draw"}, inplace=True)
        total_errors_df.set_index(['chain', 'draw', 'player_key'], inplace=True, verify_integrity=True)

        # Display all the stats calculations
        st.header("Summary of Rewards")
        bowling_summary, batting_summary = st.columns(2)
        fielding_summary, total_summary = st.columns(2)

        st.header("Summary of Error Metrics")
        bowling_error, batting_error = st.columns(2)
        fielding_error, total_error = st.columns(2)
        bowling_error_pct, batting_error_pct = st.columns(2)
        fielding_error_pct, total_error_pct = st.columns(2)

        columns_to_map = ['bowling_rewards_received', 'batting_rewards_received', 'fielding_rewards_received',
                          'total_rewards_received', 'bowling_rewards_absolute_error', 'batting_rewards_absolute_error',
                          'fielding_rewards_absolute_error', 'total_rewards_absolute_error',
                          'bowling_rewards_absolute_percentage_error',
                          'batting_rewards_absolute_percentage_error',
                          'fielding_rewards_absolute_percentage_error',
                          'total_rewards_absolute_percentage_error']

        panels_to_map = [bowling_summary, batting_summary, fielding_summary, total_summary, bowling_error,
                         batting_error, fielding_error, total_error, bowling_error_pct, batting_error_pct,
                         fielding_error_pct, total_error_pct]

        total_panels = len(panels_to_map)

        for i in range(0, total_panels):
            show_summary(columns_to_map[i], panels_to_map[i], total_errors_df[columns_to_map[i]], data_selection)


app()
