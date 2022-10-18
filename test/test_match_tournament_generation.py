import shutil

import scripts.helpers.helper_utils as helper
import utils.match_utils.data_reader_utils as reader
import pytest
import os


@pytest.fixture
def correct_file_dir():
    output_dir = "data/test/match_data/"
    helper.read_all_matches(input_file="scripts/helpers/resources/test/test_matches_correct.csv",
                            output_dir=output_dir)
    yield output_dir
    #shutil.rmtree(output_dir)


def test_correct_files(correct_file_dir):
    assert (os.path.isdir(correct_file_dir))
    tournament = reader.Tournaments("{}/tournaments.csv".format(correct_file_dir))
    matches = reader.Matches("{}/tournaments.csv".format(correct_file_dir))
    print(tournament.df.columns.values)

    expected_columns =  ["tournament", "start_date", "end_date"]
    for column in expected_columns:
        assert(column in tournament.df.columns.values)

    assert len(expected_columns) == len(tournament.df.columns.values)

