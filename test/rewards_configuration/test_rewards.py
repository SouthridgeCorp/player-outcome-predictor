import pandas as pd
import pytest
from test.conftest import get_test_cases
import os
import random


def get_generated_df(play_type, reward_type, rewards_config):
    if reward_type == "base_reward":
        expected_columns = ["outcome_index", "reward_amount"]
        if play_type == "batting":
            generated_df = rewards_config.get_batting_base_rewards()
        elif play_type == "bowling":
            generated_df = rewards_config.get_bowling_base_rewards()
        else:
            generated_df = rewards_config.get_fielding_base_rewards()
    elif reward_type == "bonus":
        expected_columns = ["outcome_index", "bonus_penalty_threshold", "bonus_penalty_cap_floor"]
        if play_type == "batting":
            generated_df = rewards_config.get_batting_bonus()
        elif play_type == "bowling":
            generated_df = rewards_config.get_bowling_bonus()
        else:
            generated_df = rewards_config.get_fielding_bonus()
    else:
        expected_columns = ["outcome_index", "bonus_penalty_threshold", "bonus_penalty_cap_floor"]
        if play_type == "batting":
            generated_df = rewards_config.get_batting_penalties()
        elif play_type == "bowling":
            generated_df = rewards_config.get_bowling_penalties()
        else:
            generated_df = rewards_config.get_fielding_penalties()

    return generated_df, expected_columns


def validate_generated_data(df_from_csv, play_type, reward_type, rewards_config):
    generated_df, expected_columns = get_generated_df(play_type, reward_type, rewards_config)

    generated_query = f'play_type == "{play_type}" and reward_type == "{reward_type}"'
    expected_df = df_from_csv.query(generated_query)[expected_columns]
    pd.testing.assert_frame_equal(generated_df, expected_df)
    return generated_df.equals(expected_df)


def update_generated_data(play_type, reward_type, rewards_config, generated_file):
    generated_df, expected_columns = get_generated_df(play_type, reward_type, rewards_config)

    if len(generated_df) == 0:
        return True

    df_from_csv = pd.read_csv(generated_file)

    df_to_update = df_from_csv.query(f"play_type == '{play_type}' and reward_type == '{reward_type}'")
    if reward_type == "base_reward":
        new_value = random.randint(100, 200)
        for index, row in df_to_update.iterrows():
            df_to_update.at[index, "reward_amount"] = new_value
            break
        generated_df.iat[0, 1] = new_value
        rewards_config.get_base_rewards(generated_df, play_type)
    else:
        new_value = random.randint(1, 100)
        for index, row in df_to_update.iterrows():
            df_to_update.at[index, "bonus_penalty_threshold"] = f"{new_value}%"
            break
        generated_df.iat[0, 1] = f"{new_value}%"
        rewards_config.set_bonus_penalty_values(generated_df, play_type, reward_type)

    if not validate_generated_data(df_to_update, play_type, reward_type, rewards_config):
        return False

    df_from_csv = pd.read_csv(generated_file)
    return validate_generated_data(df_from_csv, play_type, reward_type, rewards_config)


@pytest.mark.parametrize(
    'test_case',
    get_test_cases('app_config', 'TestRewardsConfiguration'),
    scope='class'
)
class TestRewardsConfiguration:

    def test_rewards_generation(self, setup_and_teardown, rewards_configuration, generated_file):
        test_case, config_instance = setup_and_teardown
        repo_path, generated_path, file_name = config_instance.get_rewards_info()
        assert repo_path != ""
        assert generated_path != ""
        assert file_name != ""
        assert os.path.exists(generated_file)

    @pytest.mark.parametrize("play_type", ["batting", "bowling", "fielding"])
    @pytest.mark.parametrize("reward_type", ["base_reward", "bonus", "penalty"])
    def test_rewards_queries(self, rewards_configuration, generated_file, play_type, reward_type):
        test_df = pd.read_csv(generated_file)
        assert validate_generated_data(test_df, play_type, reward_type, rewards_configuration), \
            f"Error when comparing dataframes for {play_type} and {reward_type}"

    @pytest.mark.parametrize("play_type", ["batting", "bowling", "fielding"])
    @pytest.mark.parametrize("reward_type", ["base_reward", "bonus", "penalty"])
    def test_data_updates(self, rewards_configuration, generated_file, play_type, reward_type):
        assert update_generated_data(play_type, reward_type, rewards_configuration, generated_file), \
            f"Error when updating dataframes for {play_type} and {reward_type}"
