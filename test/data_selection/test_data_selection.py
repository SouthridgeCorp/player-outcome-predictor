import pandas as pd
import pytest
from test.conftest import get_test_cases, tournaments_to_test
from data_selection.data_selection import DataSelection
from datetime import datetime
import csv


def prepare_tests(data_selection_instance, is_testing):
    tournaments = data_selection_instance.historical_data_helper.tournaments

    if is_testing:
        tournaments.set_testing_details("Big Bash League", "2017/18")
    else:
        tournaments.set_training_selected_tournament_names(["Big Bash League", "Afghanistan Premier League"])
        start_date = datetime.strptime("01/01/2018", "%d/%m/%Y").date()
        end_date = datetime.strptime("31/12/2018", "%d/%m/%Y").date()

        tournaments.set_training_window(start_date, end_date)


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

        if is_testing:
            assert len(selected_matches) == 43
        else:
            assert len(selected_matches) == 47

    @pytest.mark.parametrize('is_testing', [True, False])
    def test_playing_xi(self, data_selection_instance: DataSelection, is_testing):
        prepare_tests(data_selection_instance, is_testing)

        playing_xi = data_selection_instance.get_playing_xi_for_selected_matches(is_testing)
        expected_columns = ["team", "match_key", "player_key"]
        if is_testing:
            assert len(playing_xi) == 946
        else:
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
        if is_testing:
            assert len(innings) == 10263
        else:
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

    @pytest.mark.parametrize('is_testing', [True, False])
    def test_get_selected_teams(self, data_selection_instance: DataSelection, is_testing):
        prepare_tests(data_selection_instance, is_testing)
        selected_teams = data_selection_instance.get_selected_teams(is_testing)
        selected_teams.sort()
        if is_testing:
            testing_teams = ["Perth Scorchers", "Hobart Hurricanes", "Melbourne Stars", "Sydney Thunder",
                             "Melbourne Renegades", "Adelaide Strikers", "Sydney Sixers", "Brisbane Heat"]
            testing_teams.sort()
            assert selected_teams == testing_teams
        else:
            training_teams = ["Kandahar Knights", "Paktia Panthers", "Nangarhar Leopards", "Kabul Zwanan",
                              "Perth Scorchers", "Hobart Hurricanes", "Melbourne Stars", "Sydney Thunder",
                              "Melbourne Renegades", "Adelaide Strikers", "Sydney Sixers", "Brisbane Heat"]
            training_teams.sort()
            assert selected_teams == training_teams

    @pytest.mark.parametrize('is_testing', [True, False])
    def test_get_selected_venues(self, data_selection_instance: DataSelection, is_testing):
        prepare_tests(data_selection_instance, is_testing)
        selected_venues = data_selection_instance.get_selected_venues(is_testing)
        selected_venues.sort()
        if is_testing:
            testing_venues = ["W.A.C.A. Ground, Perth", "Melbourne Cricket Ground, Melbourne",
                              "Docklands Stadium, Melbourne", "Adelaide Oval, Adelaide", "Manuka Oval, Canberra",
                              "Bellerive Oval, Hobart", "Simonds Stadium, South Geelong, Victoria",
                              "Sydney Cricket Ground, Sydney", "Brisbane Cricket Ground, Brisbane",
                              "Sydney Showground Stadium, Sydney", "Perth Stadium, Perth",
                              "Aurora Stadium, Launceston", "Traeger Park, Alice Springs"]
            testing_venues.sort()
            assert selected_venues == testing_venues
        else:
            training_venues = ["Sharjah Cricket Stadium, Sharjah", "W.A.C.A. Ground, Perth",
                               "Melbourne Cricket Ground, Melbourne", "Docklands Stadium, Melbourne",
                               "Adelaide Oval, Adelaide", "Manuka Oval, Canberra", "Bellerive Oval, Hobart",
                               "Simonds Stadium, South Geelong, Victoria", "Sydney Cricket Ground, Sydney",
                               "Brisbane Cricket Ground, Brisbane", "Sydney Showground Stadium, Sydney",
                               "Carrara Oval, Carrara", "Perth Stadium, Perth", "Aurora Stadium, Launceston",
                               "Traeger Park, Alice Springs"]
            training_venues.sort()
            assert selected_venues == training_venues

    def test_get_all_seasons(self, data_selection_instance: DataSelection):
        expected_seasons_bbl = ["2018/19", "2017/18", "2014/15", "2013/14", "2021/22", "2019/20", "2012/13", "2016/17"]
        expected_seasons_apl = ["2018/19"]

        received_seasons_bbl = data_selection_instance.get_all_seasons("bbl")
        received_seasons_apl = data_selection_instance.get_all_seasons("apl")

        assert expected_seasons_bbl == received_seasons_bbl
        assert expected_seasons_apl == received_seasons_apl

    def test_get_seasons_by_window(self, data_selection_instance: DataSelection):
        tournaments = data_selection_instance.historical_data_helper.tournaments
        start_date = datetime.strptime("01/01/2018", "%d/%m/%Y").date()
        end_date = datetime.strptime("31/12/2018", "%d/%m/%Y").date()

        list_of_seasons = {"bbl": ["2018/19", "2017/18"],
                           "apl": ["2018/19"]}
        seasons_df = tournaments.get_season_details_for_window(start_date, end_date)
        expected_seasons_columns = ["name", "season", "number_of_matches"]
        expected_seasons_columns.sort()
        seasons_columns = list(seasons_df.columns)
        seasons_columns.sort()
        assert expected_seasons_columns == seasons_columns

        for tournament in ["Afghanistan Premier League", "Big Bash League"]:
            key = tournaments.get_key(tournament)
            expected_seasons = list_of_seasons[key]
            expected_seasons.sort()

            received_seasons = list(seasons_df[seasons_df['name'] == tournament]['season'].unique())
            received_seasons.sort()
            assert received_seasons == expected_seasons

    def test_get_season_with_start_date_df(self, data_selection_instance: DataSelection):
        tournaments = data_selection_instance.historical_data_helper.tournaments
        seasons_df = tournaments.get_tournament_and_season_details()

        expected_seasons = {"bbl": {'2012/13': "2013-01-07", '2013/14': "2014-01-16", '2014/15': "2014-12-18",
                                    '2016/17': "2017-01-25", '2017/18': "2017-12-19", '2018/19': "2018-12-19",
                                    '2019/20': "2019-12-17", '2021/22': "2022-01-19"},
                            "apl": {"2018/19": "2018-10-05"}
                            }

        for index, row in seasons_df.iterrows():
            season = row['season']
            tournament_key = row['tournament_key']
            date = row['date']
            expected_date = expected_seasons[tournament_key][season]
            assert str(date) == expected_date, f"Date mismatch tournament {tournament_key} season {season}\n" \
                                               f"expected date: {expected_date} received date: {date}"

        for tournament in ["apl", "bbl"]:
            expected_list_of_seasons = list(expected_seasons[tournament].keys())
            received_list_of_seasons = list(seasons_df[seasons_df["tournament_key"] == tournament]['season'].unique())

            expected_list_of_seasons.sort()
            received_list_of_seasons.sort()
            assert expected_list_of_seasons == received_list_of_seasons

    def test_get_previous_tournament_matches(self, data_selection_instance: DataSelection):
        # '2016/17', '2017/18', '2018/19', '2019/20',
        key = 'bbl'
        season = '2019/20'
        previous_seasons_df, previous_matches_df, previous_innings_df = \
            data_selection_instance.get_previous_tournament_matches(key, season, 3)

        assert list(previous_seasons_df['season']) == ['2018/19', '2017/18', '2016/17']
        assert previous_matches_df.shape[0] == 44 + 43 + 2
        innings_matches = list(previous_innings_df['match_key'].unique())
        innings_matches.sort()
        expected_matches = list(previous_matches_df['key'].unique())
        expected_matches.sort()
        assert innings_matches == expected_matches

        innings_columns = list(previous_innings_df.columns)
        assert 'bowling_team' in innings_columns

