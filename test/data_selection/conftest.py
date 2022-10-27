import pytest
from historical_data.singleton import Helper
from data_selection.data_selection import DataSelection

@pytest.fixture
def tournament_helper(setup_and_teardown):
    test_case, config_instance = setup_and_teardown
    tournament_helper = Helper(config_instance)
    yield tournament_helper

@pytest.fixture
def data_selection_instance(tournament_helper):
    instance = DataSelection(tournament_helper)
    yield instance