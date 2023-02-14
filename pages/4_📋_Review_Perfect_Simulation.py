import streamlit as st

import utils.page_utils as page_utils
from simulators.perfect_simulator import PerfectSimulator
from utils.app_utils import data_selection_instance, rewards_instance, prep_simulator_pages, \
    show_granularity_metrics
from rewards_configuration.rewards_configuration import RewardsConfiguration
import pandas as pd
import logging
from data_selection.data_selection import DataSelection
import altair as alt

logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)
logger = logging.getLogger(__name__)

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


def show_perfect_simulator_stats(perfect_simulator):
    return
    logger.debug("Writing stats")
    with st.spinner("Calculating Training stats"):
        with st.expander("Click to see training stats"):
            _, _, stats = perfect_simulator.get_match_state_by_balls_for_training(calculate_bowling_options=False,
                                                                                  one_hot_encoding=False)

            for key in stats.keys():
                st.markdown(f"**{key}:** {stats[key]}")


def setup_selected_players(data_selection, rewards_config, tournament_key, season, lookback_count, player_count):
    """
    Helper function to select the top X players based on total rewards and lookback to previous tournaments,
    and to save them to cache for use in later
    pages.
    :param data_selection: The data_selection instance for this app
    :param rewards_config: the rewards config instance for this app
    :param tournament_key: the tournament key for which to look back
    :param tournament_key: the tournament key for which to look back

    """

    # Get previous season details
    previous_seasons_df, previous_matches_df, previous_innings_df = \
        data_selection.get_previous_tournament_matches(tournament_key, season, lookback_count)

    if not previous_seasons_df.empty:

        # Calculate rewards for all the previous innings
        lookback_data_selection = DataSelection(data_selection.get_helper())
        lookback_data_selection.set_simulated_data(previous_matches_df, previous_innings_df)
        lookback_perfect_simulator = PerfectSimulator(lookback_data_selection, rewards_config)
        lookback_reward_df = get_perfect_simulator_data(lookback_perfect_simulator, "match", rewards_config)

        # Average out the rewards for each player
        mean_reward_df = pd.DataFrame()
        reward_grouping = lookback_reward_df.groupby('player_key')
        mean_reward_df['name'] = reward_grouping['name'].first()
        mean_reward_df['number_of_matches'] = reward_grouping['number_of_matches'].count()
        mean_reward_df['bowling_rewards'] = reward_grouping['bowling_rewards'].mean()
        mean_reward_df['batting_rewards'] = reward_grouping['batting_rewards'].mean()
        mean_reward_df['fielding_rewards'] = reward_grouping['fielding_rewards'].mean()
        mean_reward_df['total_rewards'] = reward_grouping['total_rewards'].mean()
        mean_reward_df['min_total_rewards'] = reward_grouping['total_rewards'].min()
        mean_reward_df['max_total_rewards'] = reward_grouping['total_rewards'].max()
        mean_reward_df['sd_total_rewards'] = reward_grouping['total_rewards'].std()


        # Batter == Someone with no bowling_rewards at all
        mean_reward_df['is_batter'] = mean_reward_df['bowling_rewards'] == 0
        mean_reward_df.sort_values(by='total_rewards', ascending=False, inplace=True)

        # Setup & save the group of selected players
        selected_players_for_comparison_df = mean_reward_df[['name', 'is_batter', 'number_of_matches',
                                                             'total_rewards', 'sd_total_rewards', 'min_total_rewards',
                                                             'max_total_rewards',
                                                             'bowling_rewards',
                                                             'batting_rewards', 'fielding_rewards']].head(player_count)

        st.session_state['selected_players_for_comparison'] = selected_players_for_comparison_df

        bar_chart_column, stats_column, seasons_column = st.columns(3)

        # Show the distribution of rewards across players
        with bar_chart_column:
            st.markdown("**Summary: Top Players by Average Total Rewards**")

            # Bin players into groups of 20 points
            labels = ["{0} - {1}".format(i, i + 19) for i in range(0, 140, 20)]
            selected_players_for_comparison_df["group"] = pd.cut(selected_players_for_comparison_df['total_rewards'],
                                                                 range(0, 155, 20), right=False, labels=labels)

            # Group together based on bins and show it via bar charts
            reward_label_df = pd.DataFrame()
            reward_label_grouping = selected_players_for_comparison_df.reset_index().groupby('group')
            reward_label_df['number_of_players'] = reward_label_grouping['player_key'].count()

            st.write(alt.Chart(reward_label_df.reset_index()).mark_bar().encode(
                x=alt.X('group', sort=None),
                y='number_of_players',
            ))
        with stats_column:
            st.markdown("**Stats: Top Players by Average Total Rewards**")
            number_of_batters = selected_players_for_comparison_df['is_batter'].sum()
            st.info(f"Number of Batters: _{number_of_batters}_")
            st.info(f"Number of Players selected: _{selected_players_for_comparison_df.shape[0]}_")
            st.info(f"% of batters: _{(number_of_batters / selected_players_for_comparison_df.shape[0]):.0%}_")

        with seasons_column:
            st.markdown("**Previous Seasons Identified**")
            st.dataframe(previous_seasons_df)

        st.markdown("**Raw Data: Top Players by Average Total Rewards**")

        st.dataframe(selected_players_for_comparison_df, use_container_width=True)
        with st.expander("Click to see rewards per player per match"):
            st.dataframe(lookback_reward_df, use_container_width=True)
    else:
        st.warning(f"Could not find any historical seasons before '{season}' for tournament '{tournament_key}'")


def select_key_players(rewards_config, data_selection):
    """
    Sets up the widget to select key players for use in later pages.
    """
    st.subheader("Analysis of Previous Tournaments")

    lookback, number_of_players = st.columns(2)
    with lookback:
        lookback_count = st.selectbox("Please select the number of seasons to look back:", [0, 1, 2, 3, 4, 5])
    with number_of_players:
        player_count = st.selectbox("Please select the number of players :", [0, 50, 60, 70, 80, 90, 100])
    if (lookback_count > 0) and (player_count > 0):
        tournament_key, _, season = data_selection.get_helper().tournaments.get_testing_details()
        setup_selected_players(data_selection, rewards_config, tournament_key, season, lookback_count, player_count)
    else:
        st.info("Please select a look back window & player count before proceeding.")

def app():
    data_selection = data_selection_instance()
    tournaments = data_selection.get_helper().tournaments
    rewards = rewards_instance()

    page_utils.setup_page(" Review Perfect Simulation ")

    if not prep_simulator_pages(data_selection, "Perfect Simulator"):
        return

    select_key_players(rewards, data_selection)

    st.subheader("Rewards Analysis")

    granularity, metric, metrics, error_metrics = show_granularity_metrics("perfect")

    perfect_simulator = PerfectSimulator(data_selection, rewards)

    show_perfect_simulator_stats(perfect_simulator)

    if granularity == 'None':
        st.write("Please select a valid Granularity")
    else:
        with st.spinner("Calculating Simulation Metrics.."):
            perfect_simulator_df = get_perfect_simulator_data(perfect_simulator, granularity, rewards)

        with st.spinner('Calculating Error Measures'):
            errors_df = perfect_simulator.get_error_measures(True, perfect_simulator_df, granularity,
                                                             perfect_simulator_df)

        perfect_simulator_df.to_csv("all_rewards.csv")
        number_of_players = st.slider("Select the number of top players to show:", min_value=0,
                                      max_value=len(perfect_simulator_df.index), value=30)
        st.subheader('Evaluation & Error Metrics')
        if metric not in error_metrics:
            columns_to_show = ['name', 'number_of_matches',
                               f'{metric}_expected', f'{metric}_received']
            errors_df = errors_df.sort_values(f'{metric}_expected', ascending=False)
        else:
            columns_to_show = ['name', 'number_of_matches', metric]
            errors_df = errors_df.sort_values(metric, ascending=False)

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
