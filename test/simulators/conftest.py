import pytest
from rewards_configuration.rewards_configuration import RewardsConfiguration
from data_selection.data_selection import DataSelection
from historical_data.singleton import get_helper
from simulators.perfect_simulator import PerfectSimulator

@pytest.fixture
def perfect_simulator(setup_and_teardown):
    test_case, config_instance = setup_and_teardown
    rewards_config = RewardsConfiguration(config_instance)

    input_directory = config_instance.get_input_directory()
    tournament_file_name = config_instance.get_tournament_file_name()
    player_file_name = config_instance.get_player_file_name()
    helper = get_helper(input_directory, tournament_file_name, player_file_name)

    data_selection = DataSelection(helper)

    perfect_simulator = PerfectSimulator(data_selection, rewards_config)
    yield perfect_simulator
