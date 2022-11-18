import streamlit as st
import utils.page_utils as page_utils
from utils.app_utils import data_selection_instance, rewards_instance, data_selection_summary, show_granularity_metrics
from utils.config_utils import create_utils_object
from simulators.tournament_simulator import TournamentSimulator
import logging

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

    granularity, metric, metrics, error_metrics = show_granularity_metrics("predictive")

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
            rewards_df = tournament_simulator.get_rewards(granularity)

        st.dataframe(rewards_df, use_container_width=True)


app()