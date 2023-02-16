import toml
import shutil
import pytest
import os

from utils.config_utils import ConfigUtils

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


@pytest.fixture(scope='class')
def setup_and_teardown(test_case):
    config_instance = ConfigUtils(path_to_toml_config=test_case['config_file_path'])
    yield test_case,config_instance
    teardown(config_instance)


@pytest.fixture(scope='class')
def setup_create_and_teardown(test_case):
    config_instance = ConfigUtils(path_to_toml_config=test_case['config_file_path'])
    try:
        config_instance.create_feedback_storage()
        yield test_case,config_instance
        teardown(config_instance)
    except Exception as e:
        teardown(config_instance)


def teardown(config_instance:ConfigUtils):
    config_instance.delete_feedback_storage()
    repo_path, generated_path, file_name, _ = config_instance.get_rewards_info()
    if (file_name != "") and (os.path.exists(generated_path)):
        shutil.rmtree(generated_path)
