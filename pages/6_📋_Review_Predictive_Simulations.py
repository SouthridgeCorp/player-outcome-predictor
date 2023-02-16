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
from simulators.predictive_simulator import PredictiveSimulator



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

def update_ball_counts(innings_df, source_df, perform_means):
    if perform_means:
        number_of_scenarios = innings_df.reset_index()['scenario_number'].max() + 1
    else:
        number_of_scenarios = 0
    batting_counts_df = pd.DataFrame()
    batting_grouping = innings_df.groupby("batter")
    if number_of_scenarios > 0:
        batting_counts_df['simulated_number_of_balls_faced'] = \
            batting_grouping['batter_runs'].count() / number_of_scenarios
    else:
        batting_counts_df['number_of_balls_faced'] = batting_grouping['batter_runs'].count()

    bowling_counts_df = pd.DataFrame()
    bowling_grouping = innings_df.groupby("bowler")
    if number_of_scenarios > 0:
        bowling_counts_df['simulated_number_of_balls_bowled'] = \
            bowling_grouping['batter_runs'].count() / number_of_scenarios
    else:
        bowling_counts_df['number_of_balls_bowled'] = bowling_grouping['batter_runs'].count()
    counts_df = pd.merge(bowling_counts_df, batting_counts_df, left_index=True, right_index=True, how='outer')
    counts_df.fillna(0, inplace=True)

    return pd.merge(source_df, counts_df.reset_index(), left_on='player_key', right_on='index', how='left')

def present_total_rewards_metric(players_df, raw_metrics_to_show_df, key, predictive_simulator: PredictiveSimulator):
    details_df = pd.merge(players_df,
                          raw_metrics_to_show_df[['player_key', 'name',
                                                  'absolute_error_pct',
                                                  'total_rewards_expected',
                                                  'total_rewards_received',
                                                  'total_rewards_expected_within_hdi',
                                                  'total_rewards_hdi_width',
                                                  'total_rewards_hdi_3%',
                                                  'total_rewards_hdi_97%',
                                                  'total_rewards_sd']],
                                         left_on=key, right_on=key,
                                         how='left')

    details_df = details_df[details_df['absolute_error_pct'].notna()]
    number_of_key_players = details_df['absolute_error_pct'].count()
    st.info(f"Total Number of key players in the test tournament: "
            f"{number_of_key_players}")
    players_within_hdi = \
        len(details_df[
                details_df['total_rewards_expected_within_hdi'] == True])
    st.info(f"% of players within hdi: {100 * players_within_hdi / number_of_key_players:.2f}%")

    historical_test_innings_df = predictive_simulator.data_selection.get_innings_for_selected_matches(is_testing=True)

    details_df = update_ball_counts(historical_test_innings_df, details_df, False)
    details_df = update_ball_counts(predictive_simulator.simulated_innings_df, details_df, True)

    details_df['total_rewards_error_pct'] = 0
    mask = details_df['total_rewards_expected'] != 0
    details_df.loc[mask, 'total_rewards_error_pct'] =\
        100 * (details_df['total_rewards_received'] - details_df['total_rewards_expected']) / \
        details_df['total_rewards_expected']

    details_df['diff_number_of_balls_faced'] = details_df['simulated_number_of_balls_faced'] -\
                                               details_df['number_of_balls_faced']
    details_df['diff_number_of_balls_bowled'] = details_df['simulated_number_of_balls_bowled'] - \
                                               details_df['number_of_balls_bowled']
    columns = ['name', 'absolute_error_pct',
               'total_rewards_expected_within_hdi',
               'total_rewards_hdi_width',
               'total_rewards_hdi_3%',
               'total_rewards_hdi_97%',
               'total_rewards_sd',
               'number_of_balls_bowled',
               'number_of_balls_faced',
               'simulated_number_of_balls_bowled',
               'simulated_number_of_balls_faced',
               'diff_number_of_balls_faced',
               'diff_number_of_balls_bowled',
               'total_rewards_error_pct'
               ]
    if 'is_batter' in details_df.columns:
        columns.append('is_batter')
    st.info(f"Mean error value: {details_df['total_rewards_error_pct'].mean():.2f}")
    st.dataframe(details_df[columns].sort_values(by='absolute_error_pct'),
                 use_container_width=True)

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

                    mape_data_column, focus_players_column = st.columns(2)
                    mape_barchart_column, details_column = st.columns(2)

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
                    total_rewards_stats_df.rename(columns={'sd': "total_rewards_sd",
                                                           'hdi_3%': 'total_rewards_hdi_3%',
                                                           'hdi_97%': 'total_rewards_hdi_97%'}, inplace=True)

                    raw_metrics_to_show_df = pd.merge(raw_metrics_to_show_df,
                                                      total_rewards_stats_df.reset_index()
                                                      [['player_key', 'number_of_matches',
                                                        'total_rewards_expected',
                                                        'total_rewards_received',
                                                        'total_rewards_sd',
                                                        'total_rewards_hdi_3%',
                                                        'total_rewards_hdi_97%']],
                                                      left_on='player_key', right_on='player_key')
                    raw_metrics_to_show_df['total_rewards_hdi_width'] = \
                        abs(raw_metrics_to_show_df['total_rewards_hdi_97%'] - raw_metrics_to_show_df['total_rewards_hdi_3%'])
                    raw_metrics_to_show_df['total_rewards_expected_within_hdi'] = False
                    mask = (raw_metrics_to_show_df['total_rewards_expected'] <= raw_metrics_to_show_df['total_rewards_hdi_97%']) & \
                           (raw_metrics_to_show_df['total_rewards_expected'] >= raw_metrics_to_show_df['total_rewards_hdi_3%'])
                    raw_metrics_to_show_df.loc[mask, 'total_rewards_expected_within_hdi'] = True
                    raw_metrics_to_show_df.rename(columns={error_metric_for_mape_calc: "absolute_error_pct"}, inplace=True)


                    with mape_data_column:
                        st.subheader("Key player details")
                        # Show the raw data of how many players were selected
                        st.info(f"Total Number of key players: {len(selected_players)}")
                        #select_players_with_detail = pd.merge(selected_players_for_comparison_df,
                         #                                         raw_metrics_to_show_df[['name', 'absolute_error_pct',
                          #                                                                'total_rewards_expected_within_hdi',
                           #                                                               'total_rewards_hdi_width',
                            #                                                              'total_rewards_hdi_3%',
                             #                                                             'total_rewards_hdi_97%',
                              #                                                            'total_rewards_sd']],
                               #                                   left_on='name', right_on='name',
                                #                                  how='left')
                        present_total_rewards_metric(selected_players_for_comparison_df,
                                                     raw_metrics_to_show_df, 'name', predictive_simulator)

                    with focus_players_column:
                        st.subheader("Focus player details")
                        focus_players_df = rewards.get_focus_players()

                        # Show the raw data of how many players were selected
                        st.info(f"Total Number of focus players selected: {len(focus_players_df)}")

                        #focus_players_with_detail = pd.merge(focus_players_df,
                       #                                      raw_metrics_to_show_df[['player_key', 'name',
                        #                                                              'absolute_error_pct',
                         #                                                             'total_rewards_expected_within_hdi',
                          #                                                            'total_rewards_hdi_width',
                           #                                                           'total_rewards_hdi_3%',
                            #                                                          'total_rewards_hdi_97%',
                             #                                                         'total_rewards_sd']],
                              #                                left_on='player_key', right_on='player_key',
                               #                               how='left')
                        #focus_players_with_detail.dropna(inplace=True)
                        present_total_rewards_metric(focus_players_df, raw_metrics_to_show_df, 'player_key',
                                                     predictive_simulator)

                    with details_column:
                        st.subheader("All players details")
                        st.dataframe(raw_metrics_to_show_df[['name',
                                                             'is_batter',
                                                             'total_rewards_expected',
                                                             'total_rewards_received',
                                                             'absolute_error_pct',
                                                             'group']].sort_values(by='absolute_error_pct'),
                                    use_container_width=True)


            else:
                st.warning("Please select test players from the Perfect Simulator page")

        st.info(f"Total Number of players in the current tournament: {metrics_to_show_df.shape[0]}")
        st.dataframe(metrics_to_show_df, use_container_width=True)

        number_of_players = len(metrics_to_show_df.index)
        write_top_X_to_st(number_of_players, total_errors_df, total_errors_index, reference_df=reference_df,
                          column_suffix="_received")


app()
