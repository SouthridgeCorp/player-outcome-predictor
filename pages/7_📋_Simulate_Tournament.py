import streamlit as st
import utils.page_utils as page_utils
import utils.config_utils as config_utils

def app():

    page_utils.setup_page(" Simulate Tournament ")
    st.markdown('''
        To be Released in v0.5
        - Lets the user configure an `upcoming_tournament` and use the application to produce a `reliable_simulation` 
        for the tournament. An `upcoming_tournament` is defined as:
            - `playing_teams`
            - `playing_xi_by_team_key`
            - `tournament_format`: Current version will only implement round robin league with eliminator based playoffs.
            - `focus_players`: 5 players per team for whom player counters are to be auctioned.
        - Lets the user review the `projected_sportiqo_rewards_by_player_key` for the `focus_players` and perform
        basic sensitivity analysis on the `rewards_formula_calculation_parameters`
        - To be used for discussion on design of the "fairness" metric. Once designed, it will also be shown here.
    ''')

app()