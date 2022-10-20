import scripts.helpers.cricsheet_helper
import pytest
import test.conftest
import csv
import test.scripts.conftest as conftest


def validate_missing_columns(csv_file, list_of_columns_to_verify):
    missing_columns_in_file = []
    extra_columns_in_file = []
    with open(csv_file) as file:
        csv_reader = csv.DictReader(file)
        dict_from_csv = dict(list(csv_reader)[0])
        for column in list_of_columns_to_verify:
            if column not in dict_from_csv.keys():
                missing_columns_in_file.append(column)
        for column in dict_from_csv.keys():
            if column not in list_of_columns_to_verify:
                extra_columns_in_file.append(column)

    return missing_columns_in_file, extra_columns_in_file


@pytest.mark.parametrize("tournament", test.conftest.tournaments_to_test)
def test_data_generation(tournament, output_dir, tournaments_file, players_file,
                         matches_file, playing_xi_file, innings_file, file_columns_tuple_list):
    scripts.helpers.cricsheet_helper.parse_data(tournament_key=tournament,
                                                tournament_name="Test",
                                                base_input_dir=test.conftest.BASE_INPUT_DIR,
                                                base_output_dir=output_dir)

    assert (test.conftest.validate_path_exists(tournaments_file))
    assert (test.conftest.validate_path_exists(players_file))
    assert (test.conftest.validate_path_exists(f"{output_dir}/{tournament}"))
    assert (test.conftest.validate_path_exists(matches_file))
    assert (test.conftest.validate_path_exists(playing_xi_file))
    assert (test.conftest.validate_path_exists(innings_file))

    for file_column_tuple in file_columns_tuple_list:
        missing_columns, extra_columns = validate_missing_columns(file_column_tuple[0], file_column_tuple[1])
        assert len(missing_columns) == 0, f"Columns {missing_columns} missing in {file_column_tuple[0]}"
        assert len(extra_columns) == 0, f"Extra columns {extra_columns} present in {file_column_tuple[0]}"
