from utils.config_utils import ConfigUtils
import pandas as pd
import os
import shutil
import streamlit as st


class RewardsConfiguration:
    """
    This class contains the reward configuration which is used to calculate a player's score for a tournament. A few
    key things to note:
        - All column names used in dataframes are defined as variables below (in caps), to allow for easier changes to
        column names in the future. Any future column name change should follow the same method, or find a better way
        to manage this.
        - This function provides getters for different play types, and also provides functions to set the value in the
        dataframe. These functions must be used to read / write rewards data, instead of accessing any of the class
        variables directly.
        - This class reads all its config from the 'player_outcome_predictor.rewards_configuration' section in the
        app config.
            - It looks for 'file_name' in 'generated_path' first. If the file does not exist, it copies it over
            from the 'repo_path'.
            - Any updates to rewards are persisted in 'generated_path'/'file_name'
    """
    # All column names
    PLAY_TYPE_COLUMN = "play_type"
    REWARD_TYPE_COLUMN = "reward_type"
    OUTCOME_INDEX_COLUMN = "outcome_index"
    REWARD_AMOUNT_COLUMN = "reward_amount"
    BONUS_PENALTY_THRESHOLD_COLUMN = "bonus_penalty_threshold"
    BONUS_PENALTY_CAP_FLOOR_COLUMN = "bonus_penalty_cap_floor"

    # All play values
    BATTING_VALUE = "batting"
    BOWLING_VALUE = "bowling"
    FIELDING_VALUE = "fielding"

    # All reward values
    BASE_REWARD = "base_reward"
    PENALTY = "penalty"
    BONUS = "bonus"

    # Fielding dismissal values
    FIELDING_CATCH = "Catch"
    FIELDING_STUMP = "Stumping"
    FIELDING_DRO = "Direct run out"
    FIELDING_IDRO = "Indirect run out"

    # Bowling extras values
    NO_BALL = "No ball"
    WIDE = "Wide"


    # Meta-data about columns to be used for display / slicing
    NON_EDITABLE_OUTPUT_COLUMNS = [OUTCOME_INDEX_COLUMN]
    BASE_REWARD_OUTPUT_COLUMNS = [OUTCOME_INDEX_COLUMN, REWARD_AMOUNT_COLUMN]
    BONUS_PENALTY_COLUMNS = [OUTCOME_INDEX_COLUMN, BONUS_PENALTY_THRESHOLD_COLUMN,
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
        """
        Helper function - must not be called directly outside this class. Reads rewards data from disk and resets it
        :return: None
        """
        self.df = pd.read_csv(self.rewards_file)
        self.fielding_df = self.df[self.df[self.PLAY_TYPE_COLUMN] == self.FIELDING_VALUE]
        self.bowling_df = self.df[self.df[self.PLAY_TYPE_COLUMN] == self.BOWLING_VALUE]
        self.batting_df = self.df[self.df[self.PLAY_TYPE_COLUMN] == self.BATTING_VALUE]

    def get_batting_base_rewards(self) -> pd.DataFrame:
        """
        Returns all the base_rewards associated with batting
        :return: A dataframe containing the outcome index & the corresponding batting reward
        """
        return self.batting_df[self.batting_df[self.REWARD_TYPE_COLUMN]
                               == self.BASE_REWARD][self.BASE_REWARD_OUTPUT_COLUMNS]

    def get_bowling_base_rewards(self) -> pd.DataFrame:
        """
        Returns all the base_rewards associated with bowling
        :return: A dataframe containing the outcome index & the corresponding bowling reward
        """
        return self.bowling_df[self.bowling_df[self.REWARD_TYPE_COLUMN]
                               == self.BASE_REWARD][self.BASE_REWARD_OUTPUT_COLUMNS]

    def get_fielding_base_rewards(self) -> pd.DataFrame:
        """
        Returns all the base_rewards associated with fielding
        :return: A dataframe containing the outcome index & the corresponding fielding reward
        """
        return self.fielding_df[self.fielding_df[self.REWARD_TYPE_COLUMN]
                                == self.BASE_REWARD][self.BASE_REWARD_OUTPUT_COLUMNS]

    def get_batting_penalties(self) -> pd.DataFrame:
        """
        Returns the penalty meta-data associated with batting
        :return: A dataframe containing the penalty threshold and floor
        """
        return self.batting_df[self.batting_df[self.REWARD_TYPE_COLUMN] == self.PENALTY][self.BONUS_PENALTY_COLUMNS]

    def get_bowling_penalties(self) -> pd.DataFrame:
        """
        Returns the penalty meta-data associated with bowling
        :return: A dataframe containing the penalty threshold and floor
        """
        return self.bowling_df[self.bowling_df[self.REWARD_TYPE_COLUMN] == self.PENALTY][self.BONUS_PENALTY_COLUMNS]

    def get_fielding_penalties(self) -> pd.DataFrame:
        """
        Returns the penalty meta-data associated with fielding
        :return: A dataframe containing the penalty threshold and floor
        """
        return self.fielding_df[self.fielding_df[self.REWARD_TYPE_COLUMN] == self.PENALTY][self.BONUS_PENALTY_COLUMNS]

    def get_batting_bonus(self) -> pd.DataFrame:
        """
        Returns the bonus meta-data associated with batting
        :return: A dataframe containing the bonus threshold and cap
        """
        return self.batting_df[self.batting_df[self.REWARD_TYPE_COLUMN] == self.BONUS][self.BONUS_PENALTY_COLUMNS]

    def get_bowling_bonus(self) -> pd.DataFrame:
        """
        Returns the bonus meta-data associated with bowling
        :return: A dataframe containing the bonus threshold and cap
        """
        return self.bowling_df[self.bowling_df[self.REWARD_TYPE_COLUMN] == self.BONUS][self.BONUS_PENALTY_COLUMNS]

    def get_fielding_bonus(self) -> pd.DataFrame:
        """
        Returns the bonus meta-data associated with fielding
        :return: A dataframe containing the bonus threshold and cap
        """
        return self.fielding_df[self.fielding_df[self.REWARD_TYPE_COLUMN] == self.BONUS][self.BONUS_PENALTY_COLUMNS]

    def set_base_rewards(self, df: pd.DataFrame, play_type: str):
        """
        This function updates the base_rewards for ths specified play_type
        :param df: The dataframe containing the values that need to be updated
        :param play_type: The play_type corresponding to this update, must be one of RewardsConfiguration.BATTING_VALUE,
        RewardsConfiguration.BOWLING_VALUE or RewardsConfiguration.FIELDING_VALUE
        :return: None
        """
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

    def set_bonus_penalty_values(self, df: pd.DataFrame, play_type: str, bonus_or_penalty: str):
        """
        This function updates the bonus or penalty value for ths specified play_type
        :param df: The dataframe containing the values that need to be updated
        :param play_type: The play_type corresponding to this update, must be one of RewardsConfiguration.BATTING_VALUE,
        RewardsConfiguration.BOWLING_VALUE or RewardsConfiguration.FIELDING_VALUE
        :param bonus_or_penalty: Indicate whether the update is for a bonus or a penalty, must be one of
        RewardsConfiguration.PENALTY or RewardsConfiguration.BONUS
        :return: None
        """
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
        """
        Helper function to persist all contained data to disk. Must not be called outside this class
        :return: None
        """
        self.batting_df.to_csv(self.rewards_file, index=False)
        self.bowling_df.to_csv(self.rewards_file, index=False, mode='a', header=False)
        self.fielding_df.to_csv(self.rewards_file, index=False, mode='a', header=False)
        self.read_csv()


    def get_fielding_base_rewards_for_dismissal(self, fielding_outcome):
        fielding_rewards = self.get_fielding_base_rewards()
        if fielding_outcome in [self.FIELDING_CATCH, self.FIELDING_STUMP, self.FIELDING_DRO, self.FIELDING_IDRO]:
            return fielding_rewards[fielding_rewards['outcome_index'] == fielding_outcome].iloc[0][1]
        else:
            return 0

    def get_batting_base_rewards_for_dismissal(self):
        batting_rewards_df = self.get_batting_base_rewards()
        return batting_rewards_df[batting_rewards_df['outcome_index'] == 'Dismissal'].iloc[0][1]

    def get_label_for_runs(self, runs):
        label = "Dot ball"
        if runs == 1:
            label = "Single"
        elif runs == 2:
            label = "Two"
        elif runs == 3:
            label = "Three"
        elif runs == 4:
            label = "Four"
        elif runs == 5:
            label = "Five"
        elif runs >= 6: # Any runs conceded > 6 treated with the same penalty / rewards
            label = "Six"
        return label

    def get_label_for_wickets(self, wickets):
        if wickets == 1:
            label = "1 Wicket"
        else:
            label = f"{wickets} Wickets"
        return label

    def get_batting_base_rewards_for_runs(self, runs):
        batting_rewards_df = self.get_batting_base_rewards()
        return batting_rewards_df[batting_rewards_df['outcome_index'] == self.get_label_for_runs(runs)].iloc[0][1]

    def get_bowling_base_rewards_for_runs(self, runs):
        bowling_rewards_df = self.get_bowling_base_rewards()
        return bowling_rewards_df[bowling_rewards_df['outcome_index'] == self.get_label_for_runs(runs)].iloc[0][1]

    def get_bowling_base_rewards_for_extras(self, extra):
        bowling_rewards_df = self.get_bowling_base_rewards()
        return bowling_rewards_df[bowling_rewards_df['outcome_index'] == extra].iloc[0][1]

    def get_bowling_rewards_for_wickets(self, wicket):
        bowling_rewards_df = self.get_bowling_base_rewards()
        wicket_label = self.get_label_for_wickets(wicket)
        return bowling_rewards_df[bowling_rewards_df['outcome_index'] == wicket_label].iloc[0][1]

    def get_bowling_bonus_penalty_for_economy_rate(self, bowler_economy_rate, inning_economy_rate, base_reward):
        bowler_base_reward = abs(base_reward)
        bowler_bonus = 0.0
        bowler_penalty = 0.0
        bowling_bonus_df = self.get_bowling_bonus()
        bowling_penalty_df = self.get_bowling_penalties()

        bonus_cap = float(bowling_bonus_df.iloc[0][self.BONUS_PENALTY_CAP_FLOOR_COLUMN].strip('%')) / 100
        bonus_rate = float(bowling_bonus_df.iloc[0][self.BONUS_PENALTY_THRESHOLD_COLUMN].strip('%')) / 100

        penalty_floor = float(bowling_penalty_df.iloc[0][self.BONUS_PENALTY_CAP_FLOOR_COLUMN].strip('%')) / 100
        penalty_rate = float(bowling_penalty_df.iloc[0][self.BONUS_PENALTY_THRESHOLD_COLUMN].strip('%')) / 100
        if bowler_economy_rate < (inning_economy_rate * bonus_rate):
            bowler_bonus = max(0, (bonus_rate - bowler_economy_rate / inning_economy_rate)) * bowler_base_reward
            bowler_bonus = min(bowler_bonus, bonus_cap * bowler_base_reward)
        elif bowler_economy_rate > (inning_economy_rate * penalty_rate):
            bowler_penalty = abs(min(0, (penalty_rate - bowler_economy_rate / inning_economy_rate))
                                 * bowler_base_reward)
            bowler_penalty = min(bowler_penalty, penalty_floor * bowler_base_reward)
        return bowler_bonus, bowler_penalty

    def get_batting_bonus_penalty_for_strike_rate(self, batting_strike_rate, innings_strike_rate, base_reward):
        batting_base_reward = abs(base_reward)
        batting_bonus = 0.0
        batting_penalty = 0.0
        batting_bonus_df = self.get_batting_bonus()
        batting_penalty_df = self.get_batting_penalties()

        bonus_cap = float(batting_bonus_df.iloc[0][self.BONUS_PENALTY_CAP_FLOOR_COLUMN].strip('%')) / 100
        bonus_rate = float(batting_bonus_df.iloc[0][self.BONUS_PENALTY_THRESHOLD_COLUMN].strip('%')) / 100

        penalty_floor = float(batting_penalty_df.iloc[0][self.BONUS_PENALTY_CAP_FLOOR_COLUMN].strip('%')) / 100
        penalty_rate = float(batting_penalty_df.iloc[0][self.BONUS_PENALTY_THRESHOLD_COLUMN].strip('%')) / 100

        if batting_strike_rate > (innings_strike_rate * bonus_rate):
            batting_bonus = max(0, (batting_strike_rate / innings_strike_rate) - bonus_rate) * batting_base_reward
            batting_bonus = min(batting_bonus, bonus_cap * batting_base_reward)
        elif batting_strike_rate < (innings_strike_rate * penalty_rate):
            batting_penalty = abs(min(0, (batting_strike_rate / innings_strike_rate) - penalty_rate)
                                 * batting_base_reward)
            batting_penalty = min(batting_penalty, penalty_floor * batting_base_reward)
        return batting_bonus, batting_penalty


    def get_batting_bonus_penalty_for_economy_rate(self, bowler_economy_rate, inning_economy_rate, bowler_base_reward):
        bowler_bonus = 0.0
        bowler_penalty = 0.0
        bowling_bonus_df = self.get_bowling_bonus()
        bowling_penalty_df = self.get_bowling_penalties()

        bonus_cap = float(bowling_bonus_df.iloc[0][self.BONUS_PENALTY_CAP_FLOOR_COLUMN].strip('%')) / 100
        bonus_rate = float(bowling_bonus_df.iloc[0][self.BONUS_PENALTY_THRESHOLD_COLUMN].strip('%')) / 100

        penalty_floor = float(bowling_penalty_df.iloc[0][self.BONUS_PENALTY_CAP_FLOOR_COLUMN].strip('%')) / 100
        penalty_rate = float(bowling_penalty_df.iloc[0][self.BONUS_PENALTY_THRESHOLD_COLUMN].strip('%')) / 100
        if bowler_economy_rate < (inning_economy_rate * bonus_rate):
            bowler_bonus = max(0, (bonus_rate - bowler_economy_rate / inning_economy_rate)) * bowler_base_reward
            if bowler_bonus > bonus_cap * bowler_base_reward:
                bowler_bonus = bonus_cap * bowler_base_reward
        elif bowler_economy_rate > (inning_economy_rate * penalty_rate):
            bowler_penalty = min(0, (bowler_economy_rate / inning_economy_rate - penalty_rate)) * bowler_base_reward
            if bowler_penalty < penalty_floor * bowler_base_reward:
                bowler_penalty = penalty_floor * bowler_base_reward

        return bowler_bonus, bowler_penalty


def get_rewards(static_data_config: ConfigUtils) -> RewardsConfiguration:
    """
    Helper function to get a singleton instance of the rewards config. To only be used by
    :param static_data_config: The config object to initialise the rewards config
    :return: An instance of RewardsConfiguration
    """
    if 'RewardsConfig' not in st.session_state:
        st.session_state['RewardsConfig'] = RewardsConfiguration(static_data_config)
    return st.session_state['RewardsConfig']
