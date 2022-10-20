import streamlit as st
import utils.page_utils as page_utils
import utils.config_utils as config_utils

def app():

    page_utils.setup_page(" Review Predictive Simulation Across Time")
    st.markdown('''
        Stretch Goal for v0.5
        - Pre-runs Predictive Simulation by iteratively setting the cut-off date one tournament ahead and presents a 
        graph where the x-axis represents the tournament and the y-axis represents the `error_measures` on one of the 
        available `evaluation_metrics`.
    ''')

app()