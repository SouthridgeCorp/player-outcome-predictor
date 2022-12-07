import streamlit as st
import utils.page_utils as page_utils
from utils.config_utils import create_utils_object
from utils.app_utils import data_selection_instance, rewards_instance, prep_simulator_pages, \
    get_predictive_simulator, show_granularity_metrics, show_stats, write_top_X_to_st, reset_session_states, \
    calculate_error_metrics
from simulators.perfect_simulator import PerfectSimulator
import pandas as pd
import logging


def on_inferential_model_change():
    value = st.session_state.predictive_inferential_model_checkbox
    st.session_state['predictive_use_inferential_model'] = value
    reset_session_states()


def app():
    page_utils.setup_page(" Review Predictive Simulation ")
    enable_debug = st.checkbox("Click here to enable detailed logging", value=True)
    if enable_debug:
        logging.basicConfig()
        logging.getLogger().setLevel(logging.DEBUG)

    if 'predictive_use_inferential_model' in st.session_state:
        default_use_inferential_model = st.session_state['predictive_use_inferential_model']
    else:
        default_use_inferential_model = False

    use_inferential_model = st.checkbox("Click to activate usage of inferential model "
                                        "[else default to statistical simulator]",
                                        value=default_use_inferential_model,
                                        key="predictive_inferential_model_checkbox",
                                        on_change=on_inferential_model_change)

    data_selection = data_selection_instance()
    tournaments = data_selection.get_helper().tournaments
    rewards = rewards_instance()

    if not prep_simulator_pages(data_selection, "Predictive Simulator"):
        return

    config_utils = create_utils_object()
    number_of_scenarios = config_utils.get_predictive_simulator_info()

    st.write(f"Number of scenarios: {number_of_scenarios}")

    granularity, metric, metrics, error_metrics = show_granularity_metrics("predictive")

    if granularity == 'None':
        st.write("Please select a valid Granularity")
    else:
        perfect_simulator = PerfectSimulator(data_selection, rewards)

        predictive_simulator = get_predictive_simulator(rewards,
                                                        number_of_scenarios,
                                                        use_inferential_model)


        total_errors_df = calculate_error_metrics(number_of_scenarios,
                                                  granularity,
                                                  perfect_simulator,
                                                  predictive_simulator,
                                                  use_inferential_model)

        if total_errors_df.empty:
            st.error("Please initialise and review the inferential model before proceeding")
            return

        total_errors_index = list(total_errors_df.index.names)
        total_errors_index.remove('scenario_number')
        reference_df = total_errors_df.reset_index().query('scenario_number == 0')
        reference_df.set_index(total_errors_index, inplace=True, verify_integrity=True)

        total_errors_df = total_errors_df.reset_index()

        # Remove non-numeric values
        total_errors_df = total_errors_df.drop('name', axis=1)

        # Set up the dataframe for statistical calculations
        total_errors_df = total_errors_df.reset_index()
        total_errors_df['chain'] = 0
        total_errors_df.rename(columns={"scenario_number": "draw"}, inplace=True)
        total_errors_df.set_index(['chain', 'draw'] + total_errors_index, inplace=True, verify_integrity=True)

        # Calculate stats on the metric we are interested in and also pull in some interesting columns from the
        # reference dataframe
        if metric not in error_metrics:
            metric_stats_df = show_stats(f'{metric}_received', total_errors_df, total_errors_index)
            metric_stats_df = pd.merge(reference_df[['name', 'number_of_matches', f'{metric}_expected']],
                                       metric_stats_df, left_index=True, right_index=True)
            metric_stats_df = metric_stats_df.sort_values(f'{metric}_received', ascending=False)
            st.dataframe(metric_stats_df[['name', 'number_of_matches',
                                          f'{metric}_expected', f'{metric}_received', 'sd', 'hdi_3%', 'hdi_97%']],
                         use_container_width=True)
        else:
            # Calculate the error of the mean
            split_string = metric.split("_")
            base_metric = f"{split_string[0]}_{split_string[1]}"
            is_percentage_error = split_string[-2] == "percentage"
            calculated_metric_stats_df = show_stats(f'{base_metric}_received', total_errors_df, total_errors_index)
            calculated_metric_stats_df = pd.merge(reference_df[['number_of_matches', f'{base_metric}_expected']],
                                           calculated_metric_stats_df, left_index=True, right_index=True)
            if is_percentage_error:
                calculated_metric_stats_df[f'{metric}_of_means'] \
                    = 100 * abs((calculated_metric_stats_df[f'{base_metric}_expected']
                                 - calculated_metric_stats_df[f'{base_metric}_received']) /
                                calculated_metric_stats_df[f'{base_metric}_expected'])
            else:
                calculated_metric_stats_df[f'{metric}_of_means'] \
                    = abs(calculated_metric_stats_df[f'{base_metric}_expected']
                          - calculated_metric_stats_df[f'{base_metric}_received'])

            # Calculate the mean of the errors
            metric_stats_df = show_stats(metric, total_errors_df, total_errors_index)

            # Add in number of matches & player name
            metric_stats_df = pd.merge(reference_df[['name', 'number_of_matches']],
                                       metric_stats_df, left_index=True, right_index=True)
            metric_stats_df = pd.merge(calculated_metric_stats_df[[f'{metric}_of_means']],
                                       metric_stats_df, left_index=True, right_index=True)
            metric_stats_df = metric_stats_df.sort_values(metric, ascending=False)

            # Display both error of means and mean of errors
            st.dataframe(metric_stats_df[['name', 'number_of_matches', f'{metric}_of_means', metric,
                                          'sd', 'hdi_3%', 'hdi_97%']],
                         use_container_width=True)

        number_of_players = len(metric_stats_df.index)
        write_top_X_to_st(number_of_players, total_errors_df, total_errors_index, reference_df=reference_df,
                          column_suffix="_received")


app()
