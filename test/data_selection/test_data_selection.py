import pandas as pd
import pytest
from test.conftest import get_test_cases, tournaments_to_test
from data_selection.data_selection import DataSelection
from datetime import datetime
import csv


def prepare_tests(data_selection_instance, is_testing):
    tournaments = data_selection_instance.historical_data_helper.tournaments

    if is_testing:
        tournaments.set_testing_details("Big Bash League", ["2017/18", "2018/19"])
    else:
        tournaments.set_training_selected_tournament_names(["Big Bash League", "Afghanistan Premier League"])
        start_date = datetime.strptime("01/01/2018", "%d/%m/%Y").date()
        end_date = datetime.strptime("31/12/2018", "%d/%m/%Y").date()

        tournaments.set_training_start_end_date(start_date, end_date)


@pytest.mark.parametrize(
    'test_case',
    get_test_cases('app_config', 'TestDataSelection'),
    scope='class'
)
class TestDataSelection:

    @pytest.mark.parametrize('is_testing', [True, False])
    def test_selected_matches(self, data_selection_instance: DataSelection, is_testing):
        prepare_tests(data_selection_instance, is_testing)
        selected_matches = data_selection_instance.get_selected_matches(is_testing)

        assert len(selected_matches) == 47

    @pytest.mark.parametrize('is_testing', [True, False])
    def test_playing_xi(self, data_selection_instance: DataSelection, is_testing):
        prepare_tests(data_selection_instance, is_testing)

        playing_xi = data_selection_instance.get_playing_xi_for_selected_matches(is_testing)
        expected_columns = ["team", "match_key", "player_key"]
        assert len(playing_xi) == 1034
        assert playing_xi.columns.tolist() == expected_columns, \
            f"Received columns {playing_xi.columns.tolist()}; expected {expected_columns}"

    @pytest.mark.parametrize('is_testing', [True, False])
    def test_innings(self, data_selection_instance: DataSelection, is_testing):
        prepare_tests(data_selection_instance, is_testing)

        innings = data_selection_instance.get_innings_for_selected_matches(is_testing)
        expected_columns = ['match_key', 'inning', 'over', 'ball', 'batting_team', 'batter', 'bowler', 'non_striker',
                            'batter_runs', 'extras', 'total_runs', 'non_boundary', 'is_wicket', 'dismissal_kind',
                            'player_dismissed', 'fielder', 'is_direct_runout', 'byes', 'legbyes', 'noballs', 'penalty',
                            'wides', 'team1', 'team2', 'bowling_team', 'target_runs', 'target_overs']
        expected_columns.sort()

        received_columns = innings.columns.values.tolist()
        received_columns.sort()
        assert len(innings) == 11123
        assert received_columns == expected_columns, \
            f"Received columns {received_columns};\nexpected {expected_columns}"

        assert not innings['batting_team'].equals(innings['bowling_team'])

    def test_player_universe(self, setup_and_teardown, data_selection_instance: DataSelection):
        test_case, config_instance = setup_and_teardown
        input_dir = config_instance.get_input_directory()
        prepare_tests(data_selection_instance, False)
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

        expected_columns = ["name", "featured_player", "best_rank"]
        for team in team_set:
            expected_columns.append(f"{team}_num_matches_played")
            expected_columns.append(f"{team}_num_matches_played_rank")
        expected_columns.sort()

        received_columns = list(df.columns.values)
        received_columns.sort()
        assert received_columns == expected_columns, \
            f"Received columns {received_columns}; expected {expected_columns}"

        baseline_file = test_case['baseline_file']
        expected_df = pd.read_csv(baseline_file)
        expected_df.set_index("player_key", inplace=True)

        for column in expected_columns:
            pd.testing.assert_series_equal(df[column], expected_df[column])

    def test_get_all_matches(self, data_selection_instance: DataSelection):

        all_matches_df = data_selection_instance.get_all_matches()

        assert len(all_matches_df.index) == 147

        tournaments = all_matches_df['tournament_key'].unique().tolist()
        tournaments.sort()

        expected_tournaments = tournaments_to_test
        expected_tournaments.sort()

        assert tournaments == expected_tournaments



