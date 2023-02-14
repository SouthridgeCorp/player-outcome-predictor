import streamlit as st
import utils.page_utils as page_utils
from utils.config_utils import create_utils_object
from utils.app_utils import data_selection_instance, rewards_instance, prep_simulator_pages, \
    get_predictive_simulator, show_granularity_metrics, show_stats, write_top_X_to_st, reset_session_states, \
    calculate_error_metrics
from simulators.perfect_simulator import PerfectSimulator
import pandas as pd
import logging
import altair as alt



def on_inferential_model_change():
    value = st.session_state.predictive_inferential_model_checkbox
    st.session_state['predictive_use_inferential_model'] = value
    reset_session_states()

def get_non_error_metrics(metric, total_errors_df, total_errors_index, reference_df):
    metric_stats_df = show_stats(f'{metric}_received', total_errors_df, total_errors_index)
    metric_stats_df = pd.merge(reference_df[['name', 'number_of_matches', f'{metric}_expected']],
                               metric_stats_df, left_index=True, right_index=True)
    metric_stats_df = metric_stats_df.sort_values(f'{metric}_received', ascending=False)
    metrics_to_show_df = metric_stats_df[['name', 'number_of_matches',
                                          f'{metric}_expected', f'{metric}_received', 'sd', 'hdi_3%', 'hdi_97%']]
    return metrics_to_show_df

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
            metrics_to_show_df = get_non_error_metrics(metric, total_errors_df, total_errors_index, reference_df)
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
            metric_stats_df = metric_stats_df.sort_values(metric, ascending=True)

            # Display both error of means and mean of errors
            metrics_to_show_df = metric_stats_df[['name', 'number_of_matches', f'{metric}_of_means', metric,
                                          'sd', 'hdi_3%', 'hdi_97%']]

        compare_against_test_players = False
        # Allow users to drill down if they are looking at tournament metrics
        if granularity == 'tournament':
            compare_against_test_players = st.checkbox("Check to compare against key players")

        if compare_against_test_players:
            if 'selected_players_for_comparison' in st.session_state:
                selected_players_for_comparison_df = st.session_state['selected_players_for_comparison']

                # Only work with metrics for the key player universe
                selected_players = list(selected_players_for_comparison_df.reset_index()['player_key'].unique())
                metrics_to_show_df = metrics_to_show_df.query(f"player_key in {selected_players}")
                metrics_to_show_df = \
                    pd.merge(metrics_to_show_df,
                             selected_players_for_comparison_df[['is_batter']],
                             left_on='player_key',
                             right_on='player_key')

                if metric == "total_rewards_absolute_percentage_error":
                    # If viewing the mape metric - also show a histogram of the mape
                    raw_metrics_to_show_df = metrics_to_show_df.copy()

                    # Create buckets for grouping the mape
                    labels = ["{0} - {1}".format(i, i + 10) for i in range(0, 100, 10)]
                    labels.append(">100")
                    error_metrics_for_mape_calc = ['total_rewards_absolute_percentage_error_of_means',
                                                   'total_rewards_absolute_percentage_error']

                    error_metric_for_mape_calc = st.selectbox("Please select the error metric to investigate:",
                                                              error_metrics_for_mape_calc)
                    raw_metrics_to_show_df["group"] = pd.cut(raw_metrics_to_show_df[error_metric_for_mape_calc],
                                                             range(0, 120, 10), right=False, labels=labels)
                    raw_metrics_to_show_df["group"] = raw_metrics_to_show_df["group"].fillna(">100")

                    mape_barchart_column, mape_data_column, focus_players_column = st.columns(3)
                    with mape_barchart_column:
                        # show a histogram of mape buckets
                        mape_label_df = pd.DataFrame()
                        mape_label_grouping = raw_metrics_to_show_df.reset_index().groupby('group')
                        mape_label_df['number_of_players'] = mape_label_grouping['player_key'].count()
                        st.subheader("Breakdown by mape")
                        st.write(alt.Chart(mape_label_df.reset_index()).mark_bar().encode(
                            x=alt.X('group', sort=None),
                            y='number_of_players',
                        ))

                    # Show the raw data & assert the performance against the acceptable threshold
                    st.subheader("Key Player Stats - mape drill-down")
                    mape_cutoff = int(st.text_input('mape Threshold %:', 15))
                    acceptable_mape_df = \
                        metrics_to_show_df[metrics_to_show_df[error_metric_for_mape_calc] <= mape_cutoff]
                    st.info(f"Number of players with mape < {mape_cutoff}%: "
                            f"{100 * acceptable_mape_df.shape[0]/metrics_to_show_df.shape[0]:.2f}% "
                            f"({acceptable_mape_df.shape[0]} out of "
                            f"{metrics_to_show_df.shape[0]})")
                    number_of_batters_within_mape = acceptable_mape_df.query('is_batter == True').shape[0]
                    total_number_of_batters = metrics_to_show_df.query('is_batter == True').shape[0]

                    st.info(f"Number of batters with mape < {mape_cutoff}%: "
                            f"{100 * number_of_batters_within_mape/total_number_of_batters:.2f}% "
                            f"({number_of_batters_within_mape} out of "
                            f"{total_number_of_batters})")
                    total_rewards_stats_df = \
                        get_non_error_metrics('total_rewards', total_errors_df, total_errors_index, reference_df)
                    raw_metrics_to_show_df = pd.merge(raw_metrics_to_show_df,
                                                      total_rewards_stats_df.reset_index()
                                                      [['player_key', 'number_of_matches',
                                                        'total_rewards_expected',
                                                        'total_rewards_received']],
                                                      left_on='player_key', right_on='player_key')
                    raw_metrics_to_show_df.rename(columns = {error_metric_for_mape_calc: "error_pct"}, inplace=True)

                    with mape_data_column:
                        st.subheader("Key player details")
                        # Show the raw data of how many players were selected
                        st.info(f"Total Number of key players: {len(selected_players)}")
                        select_players_with_detail = pd.merge(selected_players_for_comparison_df,
                                                                  raw_metrics_to_show_df[['name', 'error_pct']],
                                                                  left_on='name', right_on='name',
                                                                  how='left')
                        st.info(f"Total Number of key players in the test tournament: "
                                     f"{select_players_with_detail['error_pct'].count()}")
                        with st.expander("Click to see the list of key players"):
                            st.dataframe(select_players_with_detail[['name', 'is_batter', 'error_pct']],
                                         use_container_width=True)

                    with focus_players_column:
                        st.subheader("Focus player details")
                        focus_players_df = rewards.get_focus_players()

                        # Show the raw data of how many players were selected
                        st.info(f"Total Number of focus players selected: {len(focus_players_df)}")

                        focus_players_with_detail = pd.merge(focus_players_df,
                                                              raw_metrics_to_show_df[['player_key', 'name', 'error_pct']],
                                                              left_on='player_key', right_on='player_key',
                                                              how='left')
                        focus_players_with_detail.dropna(inplace=True)
                        st.info(f"Total Number of key players in the test tournament: "
                                f"{focus_players_with_detail['error_pct'].count()}")
                        with st.expander("Click to see the list of key players"):
                            st.dataframe(focus_players_with_detail[['name', 'error_pct']],
                                         use_container_width=True)


                    st.dataframe(raw_metrics_to_show_df[['name',
                                                         'is_batter',
                                                         'total_rewards_expected',
                                                         'total_rewards_received',
                                                         'error_pct',
                                                         'group']].sort_values(by='error_pct'),
                                 use_container_width=True)


            else:
                st.warning("Please select test players from the Perfect Simulator page")

        st.info(f"Total Number of players in the current tournament: {metrics_to_show_df.shape[0]}")
        st.dataframe(metrics_to_show_df, use_container_width=True)

        number_of_players = len(metrics_to_show_df.index)
        write_top_X_to_st(number_of_players, total_errors_df, total_errors_index, reference_df=reference_df,
                          column_suffix="_received")


app()
