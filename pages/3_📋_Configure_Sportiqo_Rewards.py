import streamlit as st
import utils.page_utils as page_utils
import utils.config_utils
from rewards_configuration.rewards_configuration import RewardsConfiguration
from utils.aggrid_utis import AgGridTable
import pandas as pd
import time

def update_bonus_penalty(grid_table, set_bonus_penalty_function, play_type, bonus_or_penalty):
    df = pd.DataFrame(grid_table['data'])
    set_bonus_penalty_function(df, play_type, bonus_or_penalty)

def update_base_rewards(grid_table, set_rewards_function, play_type):
    df = pd.DataFrame(grid_table['data'])
    set_rewards_function(df, play_type)
    st.sidebar.success("Base Rewards updated successfully")


def display_grid(base_rewards_function, bonus_function, penalty_function, set_rewards_function,
                 set_bonus_penalty_function, st_column, play_type):
    with st_column:
        st.header(f"{play_type.upper()} Rewards")

        st.subheader("Base Rewards")
        rewards_df = base_rewards_function()
        base_rewards_table = AgGridTable(rewards_df)
        rewards_grid = base_rewards_table.get_grid(
            f"{play_type}_base_rewards",
            editing=True,
            non_editable_columns=RewardsConfiguration.NON_EDITABLE_OUTPUT_COLUMNS)
        st.button("Update", key=f"{play_type}_button", on_click=update_base_rewards,
                  args=[rewards_grid, set_rewards_function, play_type])

        st.subheader("Bonus Threshold & Cap")
        bonus_table = AgGridTable(bonus_function())
        bonus_grid = bonus_table.get_grid(f"{play_type}_bonus", editing=True)
        st.button("Update", key=f"{play_type}_bonus_button", on_click=update_bonus_penalty,
                  args=[bonus_grid, set_bonus_penalty_function, play_type, RewardsConfiguration.BONUS])

        st.subheader("Penalty Threshold & Floor")
        penalty_table = AgGridTable(penalty_function())
        penalty_grid = penalty_table.get_grid(f"{play_type}_penalty", editing=True)
        st.button("Update", key=f"{play_type}_penalty_button", on_click=update_bonus_penalty,
                  args=[penalty_grid, set_bonus_penalty_function, play_type, RewardsConfiguration.PENALTY])


def app():
    page_utils.setup_page(" Configure Sportiqo Rewards ")

    config_utils = utils.config_utils.create_utils_object()

    rewards_config = RewardsConfiguration(config_utils)

    batting, bowling, fielding = st.columns(3)

    display_grid(rewards_config.get_batting_base_rewards,
                 rewards_config.get_batting_bonus,
                 rewards_config.get_batting_penalties,
                 rewards_config.set_base_rewards,
                 rewards_config.set_bonus_penalty_values,
                 batting,
                 RewardsConfiguration.BATTING_VALUE)

    display_grid(rewards_config.get_bowling_base_rewards,
                 rewards_config.get_bowling_bonus,
                 rewards_config.get_bowling_penalties,
                 rewards_config.set_base_rewards,
                 rewards_config.set_bonus_penalty_values,
                 bowling,
                 RewardsConfiguration.BOWLING_VALUE)

    display_grid(rewards_config.get_fielding_base_rewards,
                 rewards_config.get_fielding_bonus,
                 rewards_config.get_fielding_penalties,
                 rewards_config.set_base_rewards,
                 rewards_config.set_bonus_penalty_values,
                 fielding,
                 RewardsConfiguration.FIELDING_VALUE)


app()
