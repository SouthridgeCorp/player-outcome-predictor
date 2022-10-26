import pytest
from rewards_configuration.rewards_configuration import RewardsConfiguration

@pytest.fixture
def rewards_configuration(setup_and_teardown):
    test_case, config_instance = setup_and_teardown
    rewards_config: RewardsConfiguration = RewardsConfiguration(config_instance)
    yield rewards_config

@pytest.fixture
def generated_file(setup_and_teardown):
    test_case, config_instance = setup_and_teardown
    repo_path, generated_path, file_name = config_instance.get_rewards_info()
    generated_file_name = f"{generated_path}/{file_name}"
    yield generated_file_name