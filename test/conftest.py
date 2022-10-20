import shutil
import pytest
import os

BASE_INPUT_DIR = "resources/test/cricsheet/"
BASE_OUTPUT_DIR = "data/generated/test/match_data/cricsheet/"

tournaments_to_test = ["apl", "bbl"]

def validate_path_exists(file_name):
    return os.path.exists(file_name)


@pytest.fixture
def output_dir():
    base_output_dir = BASE_OUTPUT_DIR
    yield base_output_dir
    # Cleanup after the test
    shutil.rmtree(base_output_dir)
