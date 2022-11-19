import streamlit as st
import utils.page_utils as page_utils
from utils.app_utils import data_selection_instance, rewards_instance, data_selection_summary, show_granularity_metrics, \
    show_stats, write_top_X_to_st
from utils.config_utils import create_utils_object
from simulators.tournament_simulator import TournamentSimulator
import logging
import pandas as pd


def app():
    logging.basicConfig()
    logging.getLogger().setLevel(logging.DEBUG)

    page_utils.setup_page(" Simulate Tournament ")
    data_selection = data_selection_instance()
    tournaments = data_selection.get_helper().tournaments
    rewards = rewards_instance()

    # Show a summary of selected training & testing windows
    data_selection_summary(tournaments)

    config_utils = create_utils_object()
    tournament_simulator = TournamentSimulator(data_selection, rewards, config_utils)

    granularity, metric, metrics, error_metrics = show_granularity_metrics("tournament", show_error_metrics=False)

    if granularity == 'None':
        st.write("Please select a valid Granularity")
    else:
        with st.expander("Expand to see tournament config parameters"):
            st.markdown(f"__Using Match config from:__ *{tournament_simulator.matches_file_name}*")
            st.markdown(f"__Using Playing XI from:__ *{tournament_simulator.playing_xi_file_name}*")

            st.markdown("__Simulating the following Tournament:__")
            st.dataframe(tournament_simulator.source_matches_df, use_container_width=True)

        with st.spinner("Generating Scenarios"):
            tournament_simulator.generate_scenarios()

        with st.spinner("Generating Rewards"):
            list_of_rewards_df = tournament_simulator.get_rewards(granularity)

        all_rewards_df = pd.DataFrame()
        for rewards_df in list_of_rewards_df:
            indices = rewards_df.index.names
            rewards_df['chain'] = 0
            rewards_df = rewards_df.reset_index()
            rewards_df.rename(columns={"tournament_scenario": "draw"}, inplace=True)
            rewards_df.set_index(['chain', 'draw'] + indices, inplace=True, verify_integrity=True)
            all_rewards_df = pd.concat([all_rewards_df, rewards_df])

        reference_df = all_rewards_df.reset_index()
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


app()
