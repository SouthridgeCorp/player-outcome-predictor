import pytest
from test.conftest import get_test_cases
import os
from rewards_configuration.rewards_configuration import RewardsConfiguration



@pytest.mark.parametrize(
    'test_case',
    get_test_cases('app_config','TestRewardsConfiguration'),
    scope='class'
)
class TestRewardsConfiguration:
    def test_rewards_generation(self, setup_and_teardown):
        test_case, config_instance = setup_and_teardown

        repo_path, generated_path, file_name = config_instance.get_rewards_info()

        assert repo_path != ""
        assert generated_path != ""
        assert file_name != ""

        rewards_config = RewardsConfiguration(config_instance)
        generated_file = f"{generated_path}/{file_name}"
        assert os.path.exists(generated_file)


    def test_reward_counts(self, setup_and_teardown):
        test_case, config_instance = setup_and_teardown
        rewards_config = RewardsConfiguration(config_instance)

        assert len(rewards_config.get_batting_base_rewards()[RewardsConfiguration.OUTCOME_INDEX_COLUMN]) == 8, \
            "Batting base reward config is incorrect"
        assert len(rewards_config.get_batting_penalties()[RewardsConfiguration.BONUS_PENALTY_THRESHOLD_COLUMN]) == 1, \
            "Batting penalty config is incorrect"
        assert len(rewards_config.get_batting_bonus()[RewardsConfiguration.BONUS_PENALTY_THRESHOLD_COLUMN]) == 1, \
            "Batting bonus config is incorrect"

        assert len(rewards_config.get_bowling_base_rewards()[RewardsConfiguration.OUTCOME_INDEX_COLUMN]) == 19, \
            "Bowling base reward config is incorrect"
        assert len(rewards_config.get_bowling_penalties()[RewardsConfiguration.BONUS_PENALTY_THRESHOLD_COLUMN]) == 1, \
            "Bowling penalty config is incorrect"
        assert len(rewards_config.get_bowling_bonus()[RewardsConfiguration.BONUS_PENALTY_THRESHOLD_COLUMN]) == 1, \
            "Bowling bonus config is incorrect"

        assert len(rewards_config.get_fielding_base_rewards()[RewardsConfiguration.OUTCOME_INDEX_COLUMN]) == 4, \
            "Fielding base reward config is incorrect"
        assert len(rewards_config.get_fielding_penalties()[RewardsConfiguration.BONUS_PENALTY_THRESHOLD_COLUMN]) == 0, \
            "Fielding penalty config is incorrect"
        assert len(rewards_config.get_fielding_bonus()[RewardsConfiguration.BONUS_PENALTY_THRESHOLD_COLUMN]) == 0, \
            "Fielding bonus config is incorrect"

