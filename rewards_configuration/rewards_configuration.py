from utils.config_utils import ConfigUtils
import pandas as pd
import os
import shutil
import streamlit as st


def get_rewards(static_data_config: ConfigUtils):
    if 'RewardsConfig' not in st.session_state:
        st.session_state['RewardsConfig'] = RewardsConfiguration(static_data_config)
    return st.session_state['RewardsConfig']


class RewardsConfiguration:
    PLAY_TYPE_COLUMN = "play_type"
    REWARD_TYPE_COLUMN = "reward_type"
    OUTCOME_INDEX_COLUMN = "outcome_index"
    REWARD_AMOUNT_COLUMN = "reward_amount"
    BONUS_PENALTY_THRESHOLD_COLUMN = "bonus_penalty_threshold"
    BONUS_PENALTY_CAP_FLOOR_COLUMN = "bonus_penalty_cap_floor"

    BATTING_VALUE = "batting"
    BOWLING_VALUE = "bowling"
    FIELDING_VALUE = "fielding"

    BASE_REWARD = "base_reward"
    PENALTY = "penalty"
    BONUS = "bonus"

    NON_EDITABLE_OUTPUT_COLUMNS = [OUTCOME_INDEX_COLUMN]
    BASE_REWARD_OUTPUT_COLUMNS = [OUTCOME_INDEX_COLUMN, REWARD_AMOUNT_COLUMN]
    BONUS_PENALTY_COLUMNS = [BONUS_PENALTY_THRESHOLD_COLUMN,
                             BONUS_PENALTY_CAP_FLOOR_COLUMN]

    def __init__(self, static_data_config: ConfigUtils):
        repo_path, generated_path, file_name = static_data_config.get_rewards_info()
        repo_file = f"{repo_path}/{file_name}"
        generated_file = f"{generated_path}/{file_name}"

        if not os.path.exists(generated_file):
            if not os.path.isdir(generated_path):
                os.makedirs(generated_path)
            shutil.copyfile(repo_file, generated_file)

        self.rewards_file = generated_file
        self.read_csv()

    def read_csv(self):
        self.df = pd.read_csv(self.rewards_file)
        self.fielding_df = self.df[self.df[self.PLAY_TYPE_COLUMN] == self.FIELDING_VALUE]
        self.bowling_df = self.df[self.df[self.PLAY_TYPE_COLUMN] == self.BOWLING_VALUE]
        self.batting_df = self.df[self.df[self.PLAY_TYPE_COLUMN] == self.BATTING_VALUE]

    def get_batting_base_rewards(self) -> pd.DataFrame:
        return self.batting_df[self.batting_df[self.REWARD_TYPE_COLUMN]
                               == self.BASE_REWARD][self.BASE_REWARD_OUTPUT_COLUMNS]

    def get_bowling_base_rewards(self) -> pd.DataFrame:
        return self.bowling_df[self.bowling_df[self.REWARD_TYPE_COLUMN]
                               == self.BASE_REWARD][self.BASE_REWARD_OUTPUT_COLUMNS]

    def get_fielding_base_rewards(self) -> pd.DataFrame:
        return self.fielding_df[self.fielding_df[self.REWARD_TYPE_COLUMN]
                                == self.BASE_REWARD][self.BASE_REWARD_OUTPUT_COLUMNS]

    def get_batting_penalties(self) -> pd.DataFrame:
        return self.batting_df[self.batting_df[self.REWARD_TYPE_COLUMN] == self.PENALTY][self.BONUS_PENALTY_COLUMNS]

    def get_bowling_penalties(self) -> pd.DataFrame:
        return self.bowling_df[self.bowling_df[self.REWARD_TYPE_COLUMN] == self.PENALTY][self.BONUS_PENALTY_COLUMNS]

    def get_fielding_penalties(self) -> pd.DataFrame:
        return self.fielding_df[self.fielding_df[self.REWARD_TYPE_COLUMN] == self.PENALTY][self.BONUS_PENALTY_COLUMNS]

    def get_batting_bonus(self) -> pd.DataFrame:
        return self.batting_df[self.batting_df[self.REWARD_TYPE_COLUMN] == self.BONUS][self.BONUS_PENALTY_COLUMNS]

    def get_bowling_bonus(self) -> pd.DataFrame:
        return self.bowling_df[self.bowling_df[self.REWARD_TYPE_COLUMN] == self.BONUS][self.BONUS_PENALTY_COLUMNS]

    def get_fielding_bonus(self) -> pd.DataFrame:
        return self.fielding_df[self.fielding_df[self.REWARD_TYPE_COLUMN] == self.BONUS][self.BONUS_PENALTY_COLUMNS]

    def set_base_rewards(self, df: pd.DataFrame, play_type):
        df_to_update = None
        if play_type == self.BATTING_VALUE:
            df_to_update = self.batting_df
        elif play_type == self.BOWLING_VALUE:
            df_to_update = self.bowling_df
        elif play_type == self.FIELDING_VALUE:
            df_to_update = self.fielding_df

        updated_df = df.set_index(
            df_to_update[df_to_update[self.REWARD_TYPE_COLUMN] == self.BASE_REWARD].index)
        df_to_update.loc[list(updated_df.index.values), self.REWARD_AMOUNT_COLUMN] \
            = updated_df.loc[:, self.REWARD_AMOUNT_COLUMN]

        self.save_rewards_to_file()

    def set_bonus_penalty_values(self, df: pd.DataFrame, play_type, bonus_or_penalty):
        df_to_update = None
        if play_type == self.BATTING_VALUE:
            df_to_update = self.batting_df
        elif play_type == self.BOWLING_VALUE:
            df_to_update = self.bowling_df
        elif play_type == self.FIELDING_VALUE:
            df_to_update = self.fielding_df

        df_to_update.loc[df_to_update[self.REWARD_TYPE_COLUMN] == bonus_or_penalty,
                         self.BONUS_PENALTY_THRESHOLD_COLUMN] = df[self.BONUS_PENALTY_THRESHOLD_COLUMN].iloc[0]
        df_to_update.loc[df_to_update[self.REWARD_TYPE_COLUMN] == bonus_or_penalty,
                         self.BONUS_PENALTY_CAP_FLOOR_COLUMN] = df[self.BONUS_PENALTY_CAP_FLOOR_COLUMN].iloc[0]

        self.save_rewards_to_file()

    def save_rewards_to_file(self):
        self.batting_df.to_csv(self.rewards_file, index=False)
        self.bowling_df.to_csv(self.rewards_file, index=False, mode='a', header=False)
        self.fielding_df.to_csv(self.rewards_file, index=False, mode='a', header=False)
        self.read_csv()


