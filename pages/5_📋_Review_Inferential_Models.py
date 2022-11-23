import streamlit as st
import utils.page_utils as page_utils
from utils.config_utils import create_utils_object
from utils.app_utils import (
    data_selection_instance,
    rewards_instance,
    batter_runs_model_instance)

def choose_model_type(config_utils):
    model_type_dict = config_utils.get_batter_runs_model_info()['model_type_dict']
    model_type = st.selectbox("Choose model type",
                              key="model_type",
                              options=model_type_dict.keys())
    session_type = st.selectbox("Choose session type",
                              key="session_type",
                              options=['training','testing'])
    if session_type == 'testing':
        model_path = st.selectbox("Choose model path",
                                  key="model_path",
                                  options=model_type_dict[model_type])


def app():

    page_utils.setup_page(" Review Inferential Models ")
    config_utils = create_utils_object()
    choose_model_type(config_utils)
    batter_runs_model = batter_runs_model_instance()
    is_model_trained = batter_runs_model.get_training_status()
    if is_model_trained:
        test_performance_metrics = batter_runs_model.get_test_performance_metrics()
    else:
        batter_runs_model.train_and_save()


app()