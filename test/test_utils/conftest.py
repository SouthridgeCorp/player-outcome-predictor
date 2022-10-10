import pytest

from utils.config_utils import ConfigUtils

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
