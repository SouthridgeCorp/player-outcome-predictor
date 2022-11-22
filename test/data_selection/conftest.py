import pytest
from historical_data.singleton import Helper
from data_selection.data_selection import DataSelection
import datetime


@pytest.fixture
def tournament_helper(setup_and_teardown):
    test_case, config_instance = setup_and_teardown
    tournament_helper = Helper(config_instance)
    yield tournament_helper


@pytest.fixture
def data_selection_instance(tournament_helper):
    instance = DataSelection(tournament_helper)
    yield instance


def prepare_for_tests(data_selection_instance, is_testing):
    tournaments = data_selection_instance.historical_data_helper.tournaments

    tournaments.set_selected_tournament_names(["Big Bash League", "Afghanistan Premier League"], is_testing)
    start_date = datetime.datetime.strptime("01/01/2018", "%d/%m/%Y").date()
    end_date = datetime.datetime.strptime("31/12/2018", "%d/%m/%Y").date()

    tournaments.set_start_end_dates(start_date, end_date, is_testing)

    return start_date, end_date


def setup_training_and_testing(data_selection_instance, is_testing):
    tournaments = data_selection_instance.historical_data_helper.tournaments

    tournaments.set_selected_tournament_names(["Big Bash League", "Afghanistan Premier League"], is_testing)

    # Setup the training window
    start_date = datetime.datetime.strptime("01/01/2018", "%d/%m/%Y").date()
    end_date = datetime.datetime.strptime("31/12/2018", "%d/%m/%Y").date()

    tournaments.set_start_end_dates(start_date, end_date, is_testing)

    # Setup the testing window
    tournaments.set_selected_tournament_names(["Big Bash League"], not is_testing)
    start_date = datetime.datetime.strptime("01/01/2019", "%d/%m/%Y").date()
    end_date = datetime.datetime.strptime("31/12/2021", "%d/%m/%Y").date()

    tournaments.set_start_end_dates(start_date, end_date, not is_testing)

    return start_date, end_date
