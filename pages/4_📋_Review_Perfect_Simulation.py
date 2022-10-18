import streamlit as st
import utils.page_utils as page_utils
import utils.config_utils as config_utils

def app():

    page_utils.setup_page(" Configure Sportiqo Rewards ")
    st.markdown('''
        To be released in v0.2
        - Lets the user review `error_measures` for all `evaluation_metrics` assuming the simulator had full awareness 
        of what actually transpired in a match in the `cut_off_tournament_for_testing`. The `evaluation_metrics_by_match_key` will have the following structure:
            - `batting_statistics_by_player_key`
            - `bowling_statistics_by_player_key`
            - `fielding_statistics_by_player_key`
            - `sqortiqo_rewards_by_player_key`
        - Shows summary statistics for a few key data points:
            - `top_5_bowlers_by_team`: A dataframe showing the top 5 bowlers for each team in each tournament, as ranked by `sportiqo_rewards_by_player_key`
            - `top_5_batsmen_by_team`: A dataframe showing the top 5 batsmen for each team in each tournament, as ranked by `sportiqo_rewards_by_player_key`
            - `top_5_players_by_team`: A dataframe showing the top 5 players for each team in each tournament, as ranked by `sportiqo_rewards_by_player_key`
    ''')

app()