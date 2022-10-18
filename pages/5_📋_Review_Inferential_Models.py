import streamlit as st
import utils.page_utils as page_utils
import utils.config_utils as config_utils

def app():

    page_utils.setup_page(" Review Inferential Models ")
    st.markdown('''
        To be released in v0.3
        - Lets the user review select one of the following inferential models and review `error_measures` on `evaluation_metrics` specific to it:
            - `first_innings_batting_outcomes_model`
            - `first_innings_bowling_outcomes_model`
            - `first_innings_fielding_outcomes_model`
            - `second_innings_batting_outcomes_model`
            - `second_innings_bowling_outcomes_model`
            - `second_innings_fielding_outcomes_model`
    ''')

app()