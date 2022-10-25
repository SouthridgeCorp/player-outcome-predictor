import toml
import shutil
import pytest
import os

BASE_INPUT_DIR = "resources/test/cricsheet/"
BASE_OUTPUT_DIR = "data/generated/test/match_data/cricsheet/"

tournaments_to_test = ["apl", "bbl"]


@pytest.fixture
def tournament(request):
    return request.param


@pytest.fixture
def tournaments_file_name(output_dir):
    return "tournaments.csv"


@pytest.fixture
def tournaments_file(output_dir, tournaments_file_name):
    return f"{output_dir}/{tournaments_file_name}"


@pytest.fixture
def matches_file(output_dir, tournament):
    return f"{output_dir}/{tournament}/matches.csv"


@pytest.fixture
def players_file_name(output_dir):
    return "players.csv"

@pytest.fixture
def players_file(output_dir, players_file_name):
    return f"{output_dir}/{players_file_name}"


@pytest.fixture
def playing_xi_file(output_dir, tournament):
    return f"{output_dir}/{tournament}/playing_xi.csv"


@pytest.fixture
def innings_file(output_dir, tournament):
    return f"{output_dir}/{tournament}/innings.csv"


def validate_path_exists(file_name):
    return os.path.exists(file_name)


def get_test_cases(target_module, test_class):
    """Loads all test case definitions which are relevant to the target_module and returns them as a list"""

    ## TODO: Replace test_cases.toml with test_cases.snowflake.toml when we are ready
    test_cases = toml.load(f'resources/test/{target_module}/test_cases.toml')

    selected_test_cases = [tc for tc in test_cases['test_case'] if tc['test_class'] == test_class]
    return selected_test_cases


@pytest.fixture
def output_dir():
    base_output_dir = BASE_OUTPUT_DIR
    yield base_output_dir
    # Cleanup after the test
    shutil.rmtree(base_output_dir)
