import streamlit as st
import utils.page_utils as page_utils
import utils.config_utils as config_utils

def app():

    page_utils.setup_page(" Available Historical Data ")
    st.markdown('''
        To be released in v0.2
        - Lets the user see all `available_t20_tournaments`
        - Lets the user set a `cut_off_tournament_for_training` 
        - Lets the user set a `cut_off_tournament_for_testing`
    ''')

app()