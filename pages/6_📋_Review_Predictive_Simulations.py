import streamlit as st
import utils.page_utils as page_utils
import utils.config_utils as config_utils

def app():

    page_utils.setup_page(" Review Predictive Simulation ")
    st.markdown('''
        To be released in v0.4
        - Lets the user review all the error metrics assuming the predictive simulator only had awareness of the following
        variables in each match after the cutoff period:
            - `playing_xi_by_team_key`
            - `venue`
    ''')

app()