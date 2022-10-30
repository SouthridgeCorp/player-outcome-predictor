import streamlit as st

from historical_data.helper import Helper
from rewards_configuration.rewards_configuration import RewardsConfiguration
from utils.config_utils import ConfigUtils


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


def get_rewards(static_data_config: ConfigUtils) -> RewardsConfiguration:
    """
    Helper function to get a singleton instance of the rewards config. To only be used by
    :param static_data_config: The config object to initialise the rewards config
    :return: An instance of RewardsConfiguration
    """
    if 'RewardsConfig' not in st.session_state:
        st.session_state['RewardsConfig'] = RewardsConfiguration(static_data_config)
    return st.session_state['RewardsConfig']
