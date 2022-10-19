import csv

import scripts.helpers.cricsheet_helper
from utils.match_utils.singleton import Helper
import os
import shutil
import pytest

BASE_INPUT_DIR = "resources/test/cricsheet/"
BASE_OUTPUT_DIR = "data/generated/test/match_data/cricsheet/"


# Helper function to look for a file name
def validate_path_exists(file_name):
    return os.path.exists(file_name)


@pytest.fixture
def output_dir():
    base_output_dir = BASE_OUTPUT_DIR
    yield base_output_dir
    # Cleanup after the test
    shutil.rmtree(base_output_dir)


@pytest.fixture(params=["apl", "bbl"])
def validate_one_tournament_key(request, output_dir):
    tournament = request.param
    scripts.helpers.cricsheet_helper.parse_data(tournament_key=tournament,
                                                tournament_name="Test",
                                                base_input_dir=BASE_INPUT_DIR,
                                                base_output_dir=output_dir)

    # Ensure all expected files are generated
    matches_file = f"{BASE_OUTPUT_DIR}/{tournament}/matches.csv"
    players_file = f"{BASE_OUTPUT_DIR}/players.csv"

    assert (validate_path_exists(f"{BASE_OUTPUT_DIR}/tournaments.csv"))
    assert (validate_path_exists(players_file))
    assert (validate_path_exists(f"{BASE_OUTPUT_DIR}/{tournament}"))
    assert (validate_path_exists(matches_file))
    assert (validate_path_exists(f"{BASE_OUTPUT_DIR}/{tournament}/playing_xi.csv"))
    assert (validate_path_exists(f"{BASE_OUTPUT_DIR}/{tournament}/innings.csv"))

    # Read the files & validate the generated datasets
    helper = Helper(input_directory=output_dir)
    assert (len(helper.tournaments.artefacts.keys()) == 1)

    # Ensure the tournament is associated with the right number of matches
    matches_list = []
    with open(matches_file, "r") as file:
        matches_csv = csv.DictReader(file)
        for row in matches_csv:
            matches_list.append(row)

    assert (helper.tournaments.matches(tournament).get_number_of_matches() == len(matches_list))

    # Ensure that each player in the xi is also found in the players.csv file
    all_players = []
    with open(players_file, "r") as file:
        players_csv = csv.DictReader(file)
        for row in players_csv:
            all_players.append(row["key"])

    # Ensure that each match data is represented, the playing xi is correct & matches are associated with valid
    # number of innings
    for match in matches_list:
        team1 = match["team1"]
        team2 = match["team2"]
        match_key = match["key"]

        # get playing_xi counts
        team1_playing_xi = helper.tournaments.playing_xi(tournament).get_playing_xi(match_key, team1)
        team2_playing_xi = helper.tournaments.playing_xi(tournament).get_playing_xi(match_key, team2)

        assert len(team1_playing_xi["player_key"]) in [11, 12], \
            f"Team {team1} has {len(team2_playing_xi['player_key'])} players in match {match_key} ({tournament})"
        assert len(team2_playing_xi["player_key"]) in [11, 12], \
            f"Team {team2} has {len(team2_playing_xi['player_key'])} players in match {match_key} ({tournament})"

        player_list = list(team1_playing_xi["player_key"].unique())
        # player_list.append(list(team2_playing_xi["player_key"].unique()))

        for player_key in player_list:
            assert player_key in all_players, f"Player {player_key} not found in players.csv"

        # get innings
        innings = helper.tournaments.innings(tournament).get_innings(match_key)

        number_of_innings = len(innings["inning"].unique())
        if number_of_innings > 2:
            assert match["result_if_no_winner"] == "tie"
        elif number_of_innings == 1:
            assert match["result_if_no_winner"] == "no result"
        else:
            assert number_of_innings == 2, f"Match {match_key} ({tournament}) does not have 2 innings. " \
                                           f"'result_if_no_winner = {match['result_if_no_winner']}"


def test_single_tournaments(validate_one_tournament_key):
    pass
