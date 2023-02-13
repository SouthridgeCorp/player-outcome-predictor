import streamlit as st
import utils.page_utils as page_utils
from rewards_configuration.rewards_configuration import RewardsConfiguration
from utils.app_utils import rewards_instance, reset_session_states
from utils.aggrid_utis import AgGridTable
import pandas as pd
from st_aggrid import AgGrid
import typing


def update_base_rewards(grid_table: AgGrid,
                        set_rewards_function: typing.Callable,
                        play_type: str):
    """
    Function callback for the Update button for base reward value updates in the UI. This function assumes the
    data update happened on an AgGrid grid
    :param grid_table: The AgGrid table which contains the updated data
    :param set_rewards_function: The function callback which will be used to persist the changes in AgGrid to the
    rewards backend
    :param play_type: The play_type corresponding to this update, must be one of RewardsConfiguration.BATTING_VALUE,
    RewardsConfiguration.BOWLING_VALUE or RewardsConfiguration.FIELDING_VALUE
    :return: None
    """
    df = pd.DataFrame(grid_table['data'])
    set_rewards_function(df, play_type)
    reset_session_states(False)
    st.sidebar.success("Base Rewards updated successfully")


def display_grid(base_rewards_function, rate_multiplier_function, set_rewards_function, st_column, play_type):
    """
    Helper function to help display all the AgGrid tables for a specific play type. It also uses function callbacks
    to query data to show in the grid & to persist changes made in the grid
    :param base_rewards_function: The function callback which will be used to query base rewards data for the play type
    :param rate_multiplier_function: The function callback which will be used to calculate & display the rate multiplier
    :param set_rewards_function: The function callback which will be used to persist changes to base rewards
    :param st_column: The streamlit column where the grids will be shown
    :param play_type: The play_type corresponding to the data shown / updated, must be one of
    RewardsConfiguration.BATTING_VALUE, RewardsConfiguration.BOWLING_VALUE or RewardsConfiguration.FIELDING_VALUE
    :return: None
    """
    with st_column:
        st.header(f"{play_type.upper()} Rewards")

        st.subheader("Base Rewards")

        # Base Rewards Table
        rewards_df = base_rewards_function()
        base_rewards_table = AgGridTable(rewards_df)
        rewards_grid = base_rewards_table.get_grid(
            f"{play_type}_base_rewards",
            editing=True,
            non_editable_columns=RewardsConfiguration.NON_EDITABLE_OUTPUT_COLUMNS)

        st.button("Update", key=f"{play_type}_button", on_click=update_base_rewards,
                  args=[rewards_grid, set_rewards_function, play_type])

        if rate_multiplier_function is not None:
            # TODO: The rate multiplier grid is currently hardcoded in the RewardsConfiguration class. This should be
            # TODO: exported to a config file & support editing directly longer-term (assuming we will still calculate
            # TODO: the rewards in this app).
            if play_type == RewardsConfiguration.BATTING_VALUE:
                rate_type = "Strike"
                rate_description = "Relative Strike Rate = Strike Rate of Batter/Strike Rate of rest of team"
            else:
                rate_type = "Economy"
                rate_description = "Relative Economy Rate = Economy Rate of Bowler/Economy Rate of rest of the team"

            st.subheader(f"{rate_type} Rate Multiplier")
            rate = st.text_input(f'Enter a sample Relative {rate_type} Rate to get its multiplier', 1,
                                 key=f"{play_type}_text_input")
            multiplier = rate_multiplier_function(float(rate))
            st.markdown(f"**Base Reward Multiplier:** _{multiplier}_.")
            st.markdown(f"**Note:** _{rate_description}_")

def app():
    page_utils.setup_page(" Configure Sportiqo Rewards ")

    rewards_config = rewards_instance()

    batting, bowling, fielding = st.columns(3)

    display_grid(rewards_config.get_batting_base_rewards,
                 rewards_config.get_batting_rate_multiplier,
                 rewards_config.set_base_rewards,
                 batting,
                 RewardsConfiguration.BATTING_VALUE)

    display_grid(rewards_config.get_bowling_base_rewards,
                 rewards_config.get_bowling_rate_multiplier,
                 rewards_config.set_base_rewards,
                 bowling,
                 RewardsConfiguration.BOWLING_VALUE)

    display_grid(rewards_config.get_fielding_base_rewards,
                 None,
                 rewards_config.set_base_rewards,
                 fielding,
                 RewardsConfiguration.FIELDING_VALUE)


app()
