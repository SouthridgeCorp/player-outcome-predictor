import scripts.helpers.cricsheet_helper
import pytest
import test.conftest

@pytest.mark.parametrize("tournament", ["apl", "bbl"])
def test_data_generation(tournament, output_dir):
    scripts.helpers.cricsheet_helper.parse_data(tournament_key=tournament,
                                                tournament_name="Test",
                                                base_input_dir=test.conftest.BASE_INPUT_DIR,
                                                base_output_dir=output_dir)

    # Ensure all expected files are generated
    matches_file = f"{output_dir}/{tournament}/matches.csv"
    players_file = f"{output_dir}/players.csv"

    assert (test.conftest.validate_path_exists(f"{output_dir}/tournaments.csv"))
    assert (test.conftest.validate_path_exists(players_file))
    assert (test.conftest.validate_path_exists(f"{output_dir}/{tournament}"))
    assert (test.conftest.validate_path_exists(matches_file))
    assert (test.conftest.validate_path_exists(f"{output_dir}/{tournament}/playing_xi.csv"))
    assert (test.conftest.validate_path_exists(f"{output_dir}/{tournament}/innings.csv"))


