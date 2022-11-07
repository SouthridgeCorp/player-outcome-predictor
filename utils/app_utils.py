import streamlit as st
from data_selection.data_selection import DataSelection
from historical_data.singleton import Helper
from rewards_configuration.rewards_configuration import RewardsConfiguration
from utils.config_utils import create_utils_object, ConfigUtils


def data_selection_instance():
    """
    Helper function to get a singleton instance of the data_selection config. To only be used within streamlit
    :return: An instance of DataSelection
    """
    if 'DataSelection' not in st.session_state:
        config_utils = create_utils_object()
        # get the helper from the singleton instance
        helper = get_helper(config_utils)
        # get a data selection instance from the singleton
        st.session_state['DataSelection'] = DataSelection(helper)

    return st.session_state['DataSelection']


def rewards_instance() -> RewardsConfiguration:
    """
    Helper function to get a singleton instance of the rewards config. To only be used within streamlit
    :return: An instance of RewardsConfiguration
    """
    if 'RewardsConfig' not in st.session_state:
        config_utils = create_utils_object()
        st.session_state['RewardsConfig'] = RewardsConfiguration(config_utils)

    return st.session_state['RewardsConfig']


def get_helper(config_utils: ConfigUtils) -> Helper:
    """
    This function returns a singleton instance of the Helper (by utilising the streamlit session state).
    Note: this function only works in the streamlit context
    :param config_utils: The config_utils object used to configure the helper
    :return: A Helper class
    """
    if 'MatchUtilsHelper' not in st.session_state:
        st.session_state['MatchUtilsHelper'] = Helper(config_utils)
    return st.session_state['MatchUtilsHelper']