import pytest


@pytest.fixture
def tournament(request):
    return request.param


@pytest.fixture
def tournaments_file(output_dir):
    return f"{output_dir}/tournaments.csv"


@pytest.fixture
def matches_file(output_dir, tournament):
    return f"{output_dir}/{tournament}/matches.csv"


@pytest.fixture
def players_file(output_dir):
    return f"{output_dir}/players.csv"


@pytest.fixture
def playing_xi_file(output_dir, tournament):
    return f"{output_dir}/{tournament}/playing_xi.csv"


@pytest.fixture
def innings_file(output_dir, tournament):
    return f"{output_dir}/{tournament}/innings.csv"


@pytest.fixture
def file_columns_tuple_list(tournaments_file, players_file, matches_file, innings_file, playing_xi_file):
    tournaments_tuple = (tournaments_file, ["key", "name", "first_match_date", "last_match_date"])

    players_tuple = (players_file, ["key", "name"])

    matches_tuple = (matches_file, ["key", "tournament_key", "city", "date", "player_of_match", "venue", "season",
                                    "team1", "team2","match_number", "group", "stage", "toss_winner", "toss_decision",
                                    "winner", "result_if_no_winner", "method", "eliminator", "bowl_out", "result",
                                    "result_margin"])

    innings_tuple = (innings_file, ["match_key", "inning", "over", "ball", "batting_team", "batter", "bowler",
                                    "non_striker", "batter_runs", "extras", "total_runs", "non_boundary", "is_wicket",
                                    "dismissal_kind", "player_dismissed", "fielder", "is_direct_runout", "byes",
                                    "legbyes", "noballs", "penalty", "wides"])

    playing_xi_tuple = (playing_xi_file, ["team", "match_key", "player_key"])

    return [tournaments_tuple, players_tuple, matches_tuple, innings_tuple, playing_xi_tuple]
