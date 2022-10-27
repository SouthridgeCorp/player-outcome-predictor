import pandas as pd
import pytest
from test.conftest import get_test_cases
from historical_data.singleton import Helper
from data_selection.data_selection import DataSelection
from datetime import datetime
import csv


def prepare_for_tests(data_selection_instance, is_testing):
    tournaments = data_selection_instance.historical_data_helper.tournaments

    tournaments.set_selected_tournament_names(["Big Bash League", "Afghanistan Premier League"])
    start_date = datetime.strptime("01/01/2018", "%d/%m/%Y").date()
    end_date = datetime.strptime("31/12/2018", "%d/%m/%Y").date()

    tournaments.set_start_end_dates(start_date, end_date, is_testing)

    return start_date, end_date


@pytest.mark.parametrize(
    'test_case',
    get_test_cases('app_config', 'TestDataSelection'),
    scope='class'
)
class TestRewardsConfiguration:

    @pytest.mark.parametrize('is_testing', [True, False])
    def test_selected_matches(self, data_selection_instance: DataSelection, is_testing):
        prepare_for_tests(data_selection_instance, is_testing)
        selected_matches = data_selection_instance.get_selected_matches(is_testing)

        assert len(selected_matches) == 47

    @pytest.mark.parametrize('is_testing', [True, False])
    def test_playing_xi(self, data_selection_instance: DataSelection, is_testing):
        prepare_for_tests(data_selection_instance, is_testing)

        playing_xi = data_selection_instance.get_playing_xi_for_selected_matches(is_testing)
        expected_columns = ["team", "match_key", "player_key"]
        assert len(playing_xi) == 1034
        assert playing_xi.columns.tolist() == expected_columns, \
            f"Received columns {playing_xi.columns.tolist()}; expected {expected_columns}"

    @pytest.mark.parametrize('is_testing', [True, False])
    def test_innings(self, data_selection_instance: DataSelection, is_testing):
        start_date, end_date = prepare_for_tests(data_selection_instance, is_testing)

        innings = data_selection_instance.get_innings_for_selected_matches(is_testing)
        expected_columns = ['match_key', 'inning', 'over', 'ball', 'batting_team', 'batter', 'bowler', 'non_striker',
                            'batter_runs', 'extras', 'total_runs', 'non_boundary', 'is_wicket', 'dismissal_kind',
                            'player_dismissed', 'fielder', 'is_direct_runout', 'byes', 'legbyes', 'noballs', 'penalty',
                            'wides']
        assert len(innings) == 11123
        assert innings.columns.values.tolist() == expected_columns, \
            f"Received columns {innings.columns.tolist()}; expected {expected_columns}"

    def test_player_universe(self, setup_and_teardown, data_selection_instance: DataSelection):
        test_case, config_instance = setup_and_teardown
        input_dir = config_instance.get_input_directory()
        start_date, end_date = prepare_for_tests(data_selection_instance, False)
        df = data_selection_instance.get_frequent_players_universe()

        team_set = set()

        for tournament in ["apl", "bbl"]:
            with open(f"{input_dir}/{tournament}/matches.csv", 'r') as file:
                reader = csv.reader(file)
                first_row = True
                for row in reader:
                    if first_row:
                        first_row = False
                    else:
                        team1 = row[7]
                        team2 = row[8]
                        team_set.add(team1)
                        team_set.add(team2)

        expected_columns = ["player_key", "featured_player", "best_rank"]
        for team in team_set:
            expected_columns.append(f"{team}_num_matches_played")
            expected_columns.append(f"{team}_num_matches_played_rank")
        expected_columns.sort()

        received_columns = list(df.columns.values)
        received_columns.sort()
        assert received_columns == expected_columns, \
            f"Received columns {df.columns.tolist()}; expected {expected_columns}"

        baseline_file = test_case['baseline_file']
        expected_df = pd.read_csv(baseline_file)
        expected_df.set_index("player_key")
        expected_df = expected_df.astype(str)
        df = df.astype(str)

        for column in expected_columns:
            pd.testing.assert_series_equal(df[column], expected_df[column])
