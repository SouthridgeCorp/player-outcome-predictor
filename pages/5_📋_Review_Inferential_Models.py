import streamlit as st
import utils.page_utils as page_utils
from inferential_models.batter_runs_models import BatterRunsModel
from utils.config_utils import create_utils_object
from utils.app_utils import (
    data_selection_instance,
    rewards_instance,
    batter_runs_model_instance)

def choose_model_type(config_utils):
    model_type_dict = config_utils.get_batter_runs_model_info()['model_type_dict']
    model_type = st.selectbox("Choose model type",
                              key="model_type",
                              options=['random_forest','bayesian_inference'])
    session_type = st.selectbox("Choose session type",
                              key="session_type",
                              options=['training','testing'])

def execute_session(batter_runs_model:BatterRunsModel):
    session_type = st.session_state['session_type']
    batter_runs_model.initiate_model(st.session_state['session_type'])
    if session_type == 'training':
        batter_runs_model.run_training()
        st.write("Training completed")
    if session_type == 'testing':
        testing_stats = batter_runs_model.run_testing()
        st.write(testing_stats)


def app():
    page_utils.setup_page(" Review Inferential Models ")
    config_utils = create_utils_object()
    choose_model_type(config_utils)
    batter_runs_model = batter_runs_model_instance()




app()