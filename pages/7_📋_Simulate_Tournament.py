import streamlit as st
import utils.page_utils as page_utils
from utils.app_utils import data_selection_instance, data_selection_summary, show_granularity_metrics, \
    show_stats, write_top_X_to_st, get_tournament_simulator, has_tournament_simulator, get_granularity_list
import logging
import pandas as pd

def reset_rewards_cache():
    for granularity in get_granularity_list():
        if f'TournamentRewards_{granularity}' in st.session_state:
            del st.session_state[f'TournamentRewards_{granularity}']

def get_rewards(tournament_simulator, granularity, regenerate):
    if not regenerate and (f'TournamentRewards_{granularity}' in st.session_state):
        return st.session_state[f'TournamentRewards_{granularity}']

    logging.debug("Running the function call")
    rewards_list = tournament_simulator.get_rewards(granularity)
    st.session_state[f'TournamentRewards_{granularity}'] = rewards_list

    return rewards_list


def display_data(tournament_simulator, data_selection, regenerate):
    granularity, metric, metrics, error_metrics = show_granularity_metrics("tournament", show_error_metrics=False)

    if granularity == 'None':
        st.write("Please select a valid Granularity")
    else:
        with st.expander("Expand to see tournament config parameters"):
            st.markdown(f"__Using Match config from:__ *{tournament_simulator.matches_file_name}*")
            st.markdown(f"__Using Playing XI from:__ *{tournament_simulator.playing_xi_file_name}*")

            st.markdown("__Simulating the following Tournament:__")
            st.dataframe(tournament_simulator.source_matches_df, use_container_width=True)

        with st.spinner("Generating Rewards"):
            all_rewards_df = get_rewards(tournament_simulator, granularity, regenerate).copy()
            indices = list(all_rewards_df.index.names)
            indices.remove('tournament_scenario')
            all_rewards_df = all_rewards_df.reset_index()

            all_rewards_df['chain'] = 0
            all_rewards_df.rename(columns={"tournament_scenario": "draw"}, inplace=True)
            all_rewards_df.set_index(['chain', 'draw'] + indices, inplace=True, verify_integrity=True)

        reference_df = all_rewards_df.copy().reset_index()

        # Intentionally drop any duplicate indices because we only really want static metadata for each player
        reference_df.set_index(indices, inplace=True)

        if len(all_rewards_df.index) > 0:
            metric_stats_df = show_stats(metric, all_rewards_df, indices)

            metric_stats_df = data_selection.merge_with_players(metric_stats_df.reset_index(), 'player_key')
            metric_stats_df.set_index(indices, inplace=True, verify_integrity=True)

            metric_stats_df = metric_stats_df.sort_values(f'{metric}', ascending=False)
            st.dataframe(metric_stats_df[['name', f'{metric}', 'sd', 'hdi_3%', 'hdi_97%']],
                         use_container_width=True)

            number_of_players = len(metric_stats_df.index)
            write_top_X_to_st(number_of_players, all_rewards_df, indices, column_suffix="", reference_df=reference_df)
        else:
            st.write("Could not find any rewards metrics to report")


def app():
    page_utils.setup_page(" Simulate Tournament ")

    logging.basicConfig()
    logging.getLogger().setLevel(logging.DEBUG)

    data_selection = data_selection_instance()
    tournaments = data_selection.get_helper().tournaments

    # Show a summary of selected training & testing windows
    data_selection_summary(tournaments)

    display = False
    if has_tournament_simulator():
        display = True
        generate_scenario = st.button('Regenerate Scenario')
    else:
        st.write("Click below to generate a scenario")
        generate_scenario = st.button('Generate Scenario')

    if generate_scenario:
        reset_rewards_cache()

    if display or generate_scenario:
        tournament_simulator = get_tournament_simulator(generate_scenario)
        st.write(f'Tournament Scenarios were last generated on '
                 f'{tournament_simulator.scenario_date_time.strftime("%m/%d/%Y, %H:%M:%S")}')
        display_data(tournament_simulator, data_selection, generate_scenario)


app()
