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


def prepare_tests(data_selection_instance, is_testing):
    tournaments = data_selection_instance.historical_data_helper.tournaments

    tournaments.set_testing_details("Big Bash League", "2017/18")

    if not is_testing:
        tournaments.set_training_selected_tournament_names(["Big Bash League", "Afghanistan Premier League"])
        start_date = datetime.datetime.strptime("01/01/2018", "%d/%m/%Y").date()
        end_date = datetime.datetime.strptime("31/12/2018", "%d/%m/%Y").date()

        tournaments.set_training_window(start_date, end_date)


def setup_training_and_testing_windows(data_selection_instance):
    tournaments = data_selection_instance.historical_data_helper.tournaments

    tournaments.set_testing_details("Big Bash League", "2019/20")

    tournaments.set_training_selected_tournament_names(["Big Bash League", "Afghanistan Premier League"])
    start_date = datetime.datetime.strptime("01/01/2017", "%d/%m/%Y").date()
    end_date = datetime.datetime.strptime("31/12/2018", "%d/%m/%Y").date()

    tournaments.set_training_window(start_date, end_date)

