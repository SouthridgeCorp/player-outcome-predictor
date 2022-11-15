import streamlit as st

import utils.page_utils as page_utils
from simulators.perfect_simulator import Granularity, PerfectSimulator
from utils.app_utils import data_selection_instance, rewards_instance, data_selection_summary
from rewards_configuration.rewards_configuration import RewardsConfiguration
import pandas as pd


@st.cache
def get_perfect_simulator_data(perfect_simulator: PerfectSimulator, granularity: str,
                               rewards_config: RewardsConfiguration) -> pd.DataFrame:
    """
    Cached function call to get the simulation evaluation metrics
    :param perfect_simulator: the simulator instance to query
    :param granularity: One of the possible granularities to slice the data in
    :param rewards_config: The underlying reward config. Note this is not used by the function, but included to ensure
    the cache resets if there is a change in rewards
    :return The dataframe representing the perfect simulator data
    """
    return perfect_simulator.get_simulation_evaluation_metrics_by_granularity(True, granularity)


def app():
    data_selection = data_selection_instance()
    tournaments = data_selection.get_helper().tournaments
    rewards = rewards_instance()

    page_utils.setup_page(" Review Perfect Simulation ")

    # Show a summary of selected training & testing windows
    data_selection_summary(tournaments)

    granularity_select, metric_select = st.columns(2)

    with granularity_select:
        granularity_list = ['None', Granularity.TOURNAMENT, Granularity.STAGE, Granularity.MATCH, Granularity.INNING]
        granularity = st.selectbox("Please select the granularity for reviewing Simulator stats", granularity_list)

    with metric_select:
        metric_list = ['bowling_rewards', 'batting_rewards', 'fielding_rewards', 'total_rewards']
        metric = st.selectbox("Please select the metric to review", metric_list)

    if granularity == 'None':
        st.write("Please select a valid Granularity")
    else:

        perfect_simulator = PerfectSimulator(data_selection, rewards)

        with st.spinner("Calculating Simulation Metrics.."):
            perfect_simulator_df = get_perfect_simulator_data(perfect_simulator, granularity, rewards)

        with st.spinner('Calculating Error Measures'):
            errors_df = perfect_simulator.get_error_measures(True, perfect_simulator_df, granularity,
                                                             perfect_simulator_df)

        number_of_players = st.slider("Select the number of top players to show:", min_value=0,
                                      max_value=len(perfect_simulator_df.index), value=30)

        st.subheader('Evaluation & Error Metrics')
        columns_to_show = ['name', 'number_of_matches', metric, f'{metric}_absolute_error',
                           f'{metric}_absolute_percentage_error']
        st.dataframe(errors_df[columns_to_show], use_container_width=True)

        top_players_column, top_batters_column, top_bowlers_column = st.columns(3)

        with top_players_column:
            perfect_simulator_df = perfect_simulator_df.sort_values('total_rewards', ascending=False)
            st.subheader(f'Top {number_of_players} Players')
            st.dataframe(perfect_simulator_df[['name', 'total_rewards']].head(number_of_players),
                         use_container_width=True)

        with top_bowlers_column:
            perfect_simulator_df = perfect_simulator_df.sort_values('bowling_rewards', ascending=False)
            st.subheader(f'Top {number_of_players} Bowlers')
            st.dataframe(perfect_simulator_df[['name', 'bowling_rewards']].head(number_of_players),
                         use_container_width=True)

        with top_batters_column:
            perfect_simulator_df = perfect_simulator_df.sort_values('batting_rewards', ascending=False)
            st.subheader(f'Top {number_of_players} Batters')
            st.dataframe(perfect_simulator_df[['name', 'batting_rewards']].head(number_of_players),
                         use_container_width=True)


app()
