import pytest
from rewards_configuration.rewards_configuration import RewardsConfiguration
from data_selection.data_selection import DataSelection
from historical_data.helper import Helper
from simulators.perfect_simulator import PerfectSimulator

@pytest.fixture
def perfect_simulator(setup_and_teardown):
    test_case, config_instance = setup_and_teardown
    rewards_config = RewardsConfiguration(config_instance)

    helper = Helper(config_instance)

    data_selection = DataSelection(helper)

    perfect_simulator = PerfectSimulator(data_selection, rewards_config)
    yield perfect_simulator
