from test.conftest import get_test_cases
import pytest
from test.data_selection.conftest import prepare_for_tests, setup_training_and_testing
import pandas as pd
import logging
import datetime


@pytest.mark.parametrize(
    'test_case',
    get_test_cases('app_config', 'TestPerfectSimulator'),
    scope='class'
)
class TestPerfectSimulator:

    def get_bowler_penalty_for_runs(row):
        total_runs = row["total_runs"]
        batter_runs = row["batter_runs"]
        extras = row["extras"]
        wides = row["wides"]
        no_ball = row["noballs"]
        non_boundary = row["non_boundary"]

        outcome_index = ""
        if total_runs == 0:
            outcome_index = "0"
        else:
            # Assumption: If a batsman runs on a no-ball or wide, the no-ball takes precedence
            if extras > 0:
                if no_ball == 1:
                    if batter_runs > 0:
                        outcome_index += f"{batter_runs}-b,"
                    if extras > 0:
                        outcome_index += f"{extras}-"
                    outcome_index += f"nb"
                elif wides == 1:
                    outcome_index = f"{total_runs}-w"
                else:
                    outcome_index = f"{total_runs}-oe"
            else:
                outcome_index = f"{total_runs}-b"
        return outcome_index

    def bowling_outcome(row):
        total_runs = row["total_runs"]

        is_wicket = row["is_wicket"]
        dismissal_kind = row["dismissal_kind"]
        is_direct_runout = row["is_direct_runout"]

        # Assumption: If there are wickets & runs on the same ball, the wicket takes precedence
        if is_wicket == 1:
            if dismissal_kind == "stumped":
                outcome_index = "W-bs"
            elif dismissal_kind == "caught":
                outcome_index = "W-bc"
            elif dismissal_kind == "run out":
                if (pd.isna(is_direct_runout)) or is_direct_runout == 0:
                    outcome_index = "W-idro"
                else:
                    outcome_index = "W-dro"
            elif (dismissal_kind == "bowled") or (dismissal_kind == "caught and bowled"):
                outcome_index = "W-b"
            else:
                outcome_index = "W-others"
            if total_runs > 0:
                outcome_index = f"{TestPerfectSimulator.get_bowler_penalty_for_runs(row)},{outcome_index}"
        else:
            outcome_index = TestPerfectSimulator.get_bowler_penalty_for_runs(row)

        return outcome_index

    @pytest.mark.parametrize('is_testing', [True, False])
    def test_get_bowling_outcomes_by_ball_and_innings(self, perfect_simulator, setup_and_teardown, is_testing):
        prepare_for_tests(perfect_simulator.data_selection, is_testing)
        df = perfect_simulator.get_bowling_outcomes_by_ball_and_innings(is_testing)

        for index, row in df.iterrows():
            expected_bowling_outcome = TestPerfectSimulator.bowling_outcome(row)
            received_bowling_outcome = row['bowling_outcome_index']
            assert received_bowling_outcome == expected_bowling_outcome, f"Outcomes don't match for {index}. " \
                                                                         f"Exepcted: {expected_bowling_outcome} but " \
                                                                         f"Received: {received_bowling_outcome}"

    @pytest.mark.parametrize('is_testing', [True, False])
    def test_get_match_state_by_ball_and_innings(self, perfect_simulator, setup_and_teardown, is_testing):
        setup_training_and_testing(perfect_simulator.data_selection, is_testing)

        start_date = datetime.datetime.strptime("01/01/1999", "%d/%m/%Y").date()
        end_date = datetime.datetime.strptime("31/12/2022", "%d/%m/%Y").date()

        tournaments = perfect_simulator.data_selection.historical_data_helper.tournaments

        tournaments.set_start_end_dates(start_date, end_date, True)


        match_state_df = perfect_simulator.get_match_state_by_ball_and_innings(is_testing)
        player_universe_df = perfect_simulator.data_selection.get_frequent_players_universe()

        player_ids = player_universe_df[player_universe_df['featured_player'] == True].index.tolist()

        columns = list(match_state_df.columns.values)

        venue_set = set(perfect_simulator.data_selection.get_selected_venues(is_testing=False))
        batter_column_count = 0
        bowler_column_count = 0
        mvp_columns = set()
        team_columns = set()
        bowling_teams = set()
        batting_teams = set()
        number_of_overs = 0
        number_of_balls = 0
        expected_venue_set = set()
        for column in columns:
            if column.startswith("batter_"):
                batter_column_count += 1
                mvp_columns.add(column[7:])
            if column.startswith("bowler_"):
                bowler_column_count += 1
                mvp_columns.add(column[7:])
            if column.startswith('batting_team_'):
                team = column[len('batting_team_'):]
                team_columns.add(team)
                batting_teams.add(team)
            if column.startswith('bowling_team_'):
                team = column[len('bowling_team_'):]
                team_columns.add(team)
                bowling_teams.add(team)
            if column.startswith('over_number_'):
                number_of_overs += 1
            if column.startswith('ball_number_in_over_'):
                number_of_balls += 1
            if column.startswith('venue_'):
                expected_venue_set.add(column[len('venue_'):])

        diff = list(set(player_ids) - mvp_columns)
        assert len(diff) == 0
        assert batter_column_count == 1 + (len(player_ids))
        assert bowler_column_count == 1 + (len(player_ids))

        training_teams_set = set(perfect_simulator.data_selection.get_selected_teams(is_testing=False))
        training_teams_set.add('not_in_training')

        assert len(list(team_columns - training_teams_set)) == 0
        assert len(list(bowling_teams - training_teams_set)) == 0
        assert len(list(batting_teams - training_teams_set)) == 0
        assert number_of_overs == 21
        assert number_of_balls == 7

        assert len(list(venue_set - expected_venue_set)) == 0

        for g, g_df in match_state_df.groupby(['match_key']):
            g_df = g_df.reset_index()
            team1_runs_scored = g_df[g_df['inning'] == 1].iloc[-1]['current_total']
            team1_wickets = g_df[g_df['inning'] == 1].iloc[-1]['wickets_fallen']
            if 2 in g_df['inning'].values:
                team2_runs_scored = g_df[g_df['inning'] == 2].iloc[-1]['current_total']
                team2_wickets = g_df[g_df['inning'] == 2].iloc[-1]['wickets_fallen']

                if g == 1152518:  # Sydney Thunder vs Sydney Sixers 24 Dec 2018
                    assert team1_runs_scored == 169
                    assert team1_wickets == 9
                    assert team2_runs_scored == 148
                    assert team2_wickets == 9

    def bowling_to_batting_outcomes_converter(df, innings_df):
        df['batting_outcome_index_expected'] = df.apply(
            lambda x: TestPerfectSimulator.convert_bowling_to_batting_df(x, innings_df), axis=1)

    def convert_bowling_to_batting_df(row, innings_df):
        bowling_outcome_index = row['bowling_outcome_index']
        index = row.name
        batter = row['batter']
        dismissed = innings_df.loc(axis=0)[index]['player_dismissed']
        batting_outcome_index = "0"
        if bowling_outcome_index.startswith("W"):
            if dismissed == batter:
                batting_outcome_index = "W"
        elif bowling_outcome_index.endswith("-b"):
            batting_outcome_index = bowling_outcome_index
        elif bowling_outcome_index == "0":
            batting_outcome_index = "0"
        else:
            if "," in bowling_outcome_index:

                runs = bowling_outcome_index.split(",")[0]
                if "-b" in runs:
                    batting_outcome_index = f"{runs.split('-')[0]}-b"
                    if dismissed == batter:
                        batting_outcome_index += ",W"
                else:
                    if dismissed == batter:
                        batting_outcome_index = "W"
            else:
                batting_outcome_index = "E"

        return batting_outcome_index

    @pytest.mark.parametrize('is_testing', [True, False])
    def test_get_batting_outcomes_by_ball_and_innings(self, perfect_simulator, is_testing):
        prepare_for_tests(perfect_simulator.data_selection, is_testing)

        df = perfect_simulator.get_batting_outcomes_by_ball_and_innings(is_testing)

        expected_df = perfect_simulator.get_bowling_outcomes_by_ball_and_innings(is_testing)
        innings_df = perfect_simulator.data_selection.get_innings_for_selected_matches(is_testing)
        index_columns = ['match_key', 'inning', 'over', 'ball']
        innings_df.set_index(index_columns, inplace=True)

        TestPerfectSimulator.bowling_to_batting_outcomes_converter(expected_df, innings_df)

        df = pd.merge(df, expected_df['batting_outcome_index_expected'], left_index=True, right_index=True)

        assert df['batter_outcome_index'].equals(df['batting_outcome_index_expected'])

        non_striker_df = df[(df["player_dismissed"].notna()) & (df["player_dismissed"] == df['non_striker'])]

        assert list(non_striker_df['non_striker_outcome_index'].unique()) == ['W']

    def bowling_to_fielding_outcomes_converter(df, innings_df):
        df['fielding_outcome_index_expected'] \
            = df.apply(lambda x: TestPerfectSimulator.convert_bowling_to_fielding_df(x, innings_df), axis=1)

    def convert_bowling_to_fielding_df(row, innings_df):
        bowling_outcome_index = row['bowling_outcome_index']
        fielder = innings_df.loc(axis=0)[row.name]['fielder']
        fielding_outcome_index = 'nfo'
        if not pd.isna(fielder):
            if "," in bowling_outcome_index:
                fielding_outcome_index = bowling_outcome_index.split(",")[1]
            else:
                fielding_outcome_index = bowling_outcome_index

        return fielding_outcome_index

    @pytest.mark.parametrize('is_testing', [True, False])
    def test_get_fielding_outcomes_by_ball_and_innings(self, perfect_simulator, is_testing):
        prepare_for_tests(perfect_simulator.data_selection, is_testing)

        df = perfect_simulator.get_fielding_outcomes_by_ball_and_innings(is_testing)

        expected_df = perfect_simulator.get_bowling_outcomes_by_ball_and_innings(is_testing)
        innings_df = perfect_simulator.data_selection.get_innings_for_selected_matches(is_testing)
        index_columns = ['match_key', 'inning', 'over', 'ball']
        innings_df.set_index(index_columns, inplace=True)

        TestPerfectSimulator.bowling_to_fielding_outcomes_converter(expected_df, innings_df)

        df = pd.merge(df, expected_df['fielding_outcome_index_expected'], left_index=True, right_index=True)

        assert df['fielding_outcome_index'].equals(df['fielding_outcome_index_expected'])

    @pytest.mark.parametrize('is_testing', [True, False])
    def test_get_outcomes_by_ball_and_innings(self, perfect_simulator, is_testing):
        prepare_for_tests(perfect_simulator.data_selection, is_testing)

        df = perfect_simulator.get_outcomes_by_ball_and_innings(is_testing)

        expected_columns = ['batter', 'batting_team', 'batter_runs', 'extras', 'total_runs', 'non_boundary',
                            'is_wicket', 'dismissal_kind', 'bowling_team', 'fielder',
                            'is_direct_runout', 'byes', 'legbyes', 'noballs', 'penalty', 'wides', 'player_dismissed',
                            'bowler', 'non_striker', 'bowling_outcome_index', 'batter_outcome_index',
                            'non_striker_outcome_index', 'fielding_outcome_index']
        expected_columns.sort()
        received_columns = df.columns.values.tolist()
        received_columns.sort()

        assert expected_columns == received_columns, f"Expected: {expected_columns}\nReceived: {received_columns}"

    def test_get_outcomes_by_player_and_innings(self, perfect_simulator, setup_and_teardown):
        is_testing = False
        prepare_for_tests(perfect_simulator.data_selection, is_testing)

        df = perfect_simulator.get_outcomes_by_player_and_innings(is_testing)

        expected_columns = ['batting_total_runs', 'economy_rate', 'number_of_overs', 'stage', 'strike_rate',
                            'total_balls', 'total_runs', 'tournament_key', 'wickets_taken']

        expected_columns.sort()
        received_columns = df.columns.values.tolist()
        received_columns.sort()

        assert expected_columns == received_columns, f"Expected: {expected_columns}\nReceived: {received_columns}"

        strike_rate_df = df[(df["strike_rate"].notna())]

        assert strike_rate_df['economy_rate'].isna().unique().tolist() == [True]
        assert strike_rate_df['wickets_taken'].isna().unique().tolist() == [True]

        economy_rate_df = df[(df["economy_rate"].notna())]

        assert economy_rate_df['strike_rate'].isna().unique().tolist() == [True]
        assert economy_rate_df['wickets_taken'].isna().unique().tolist() == [False]

        assert expected_columns == received_columns, f"Expected: {expected_columns}\nReceived: {received_columns}"

    @pytest.mark.parametrize('is_testing', [True, False])
    def test_get_outcomes_by_team_and_innings(self, perfect_simulator, is_testing):
        prepare_for_tests(perfect_simulator.data_selection, is_testing)

        df = perfect_simulator.get_outcomes_by_team_and_innings(is_testing)

        expected_columns = ['inning_batting_total_runs', 'inning_economy_rate', 'inning_number_of_overs',
                            'inning_strike_rate', 'inning_total_balls', 'inning_total_runs']
        expected_columns.sort()
        received_columns = df.columns.values.tolist()
        received_columns.sort()

        assert expected_columns == received_columns, f"Expected: {expected_columns}\nReceived: {received_columns}"

    def get_expected_batting_rewards(self, batting_outcome):
        expected_base_reward = 0
        if batting_outcome == '0' or (batting_outcome == 'E'):
            expected_base_reward = -1
        elif batting_outcome == '1-b':
            expected_base_reward = 0
        elif batting_outcome == '2-b':
            expected_base_reward = 1
        elif batting_outcome == '3-b':
            expected_base_reward = 2
        elif batting_outcome == '4-b':
            expected_base_reward = 4
        elif batting_outcome == '5-b':
            expected_base_reward = 1
        elif batting_outcome == '6-b':
            expected_base_reward = 8
        elif batting_outcome == 'W':
            expected_base_reward = -6
        elif batting_outcome.endswith('W'):
            runs = batting_outcome.split(",")[0]
            expected_base_reward = -5 + self.get_expected_batting_rewards(runs)
        return expected_base_reward

    def get_expected_bowling_rewards(self, row):
        total_runs = row['total_runs']
        reward = 0
        if total_runs == 0:
            reward = 2
        elif total_runs == 1:
            reward = 1
        elif total_runs == 2:
            reward = 0
        elif total_runs == 3:
            reward = -1
        elif total_runs == 4:
            reward = -3
        elif total_runs == 5:
            reward = 0
        elif total_runs >= 6:
            reward = -6

        wides = row["wides"]
        no_ball = row["noballs"]
        if no_ball == 1:
            reward += -3
        if wides == 1:
            reward += -1

        return reward

    def get_expected_fielding_rewards(self, row):
        fielding_outcome = row['fielding_outcome_index']
        reward = 0
        if fielding_outcome.startswith("W"):
            wicket_type = fielding_outcome[2:]
            if wicket_type == 'bc':
                reward = 1
            elif wicket_type == 'bs':
                reward = 2
            elif wicket_type == 'dro':
                reward = 2
            else:
                reward = 1
        return reward

    @pytest.mark.parametrize('is_testing', [True, False])
    def test_base_rewards(self, perfect_simulator, is_testing):
        prepare_for_tests(perfect_simulator.data_selection, is_testing)

        base_rewards_df, bonus_penalty_df = perfect_simulator.get_rewards_components(is_testing, generate_labels=True)

        for index, row in base_rewards_df.iterrows():
            expected_batting_reward = self.get_expected_batting_rewards(row['batter_outcome_index'])
            received_batting_base_reward = row['batter_base_rewards']
            assert expected_batting_reward == received_batting_base_reward, f"Input: {row}"

            expected_bowling_reward = self.get_expected_bowling_rewards(row)
            received_bowling_reward = row['bowling_base_rewards']
            assert expected_bowling_reward == received_bowling_reward, f"Input: {row}"

            expected_fielding_reward = self.get_expected_fielding_rewards(row)
            received_fielding_reward = row['fielding_base_rewards']
            assert expected_fielding_reward == received_fielding_reward, f"Input: {row}"

        non_striker_df = base_rewards_df[(base_rewards_df["player_dismissed"].notna())
                                         & (base_rewards_df["player_dismissed"] == base_rewards_df['non_striker'])]
        assert non_striker_df['non_striker_base_rewards'].unique().tolist() == [-5]

        for index, row in bonus_penalty_df.iterrows():
            if pd.isna(row['bowling_rewards']):
                assert pd.isna(row['bowling_base_rewards'] + row['bowling_bonus_wickets'] \
                                            + row['bowling_bonus'] - row['bowling_penalty'])
            else:
                assert row['bowling_rewards'] == row['bowling_base_rewards'] + row['bowling_bonus_wickets'] \
                                                + row['bowling_bonus'] - row['bowling_penalty']
            print ('hello')

    @pytest.mark.parametrize('is_testing', [True, False])
    @pytest.mark.parametrize('granularity, expected_columns',
                             [('tournament', ['player_key', 'tournament_key', 'bowling_rewards',
                                              'batting_rewards', 'fielding_rewards',
                                              'total_rewards']),
                              ('tournament_stage', ['player_key', 'tournament_key', 'stage', 'bowling_rewards',
                                                    'batting_rewards', 'fielding_rewards', 'total_rewards']),
                              ('match', ['player_key', 'tournament_key', 'stage', 'match_key', 'bowling_rewards',
                                         'batting_rewards', 'fielding_rewards', 'total_rewards']),
                              ('innings', ['player_key', 'tournament_key', 'stage', 'match_key', 'inning',
                                           'bowling_rewards', 'batting_rewards', 'fielding_rewards', 'total_rewards'])])
    def test_get_simulation_evaluation_metrics_by_granularity(self, perfect_simulator, is_testing, granularity,
                                                              expected_columns):

        prepare_for_tests(perfect_simulator.data_selection, is_testing)
        rewards_df = perfect_simulator.get_simulation_evaluation_metrics_by_granularity(is_testing, granularity)

        rewards_df = rewards_df.reset_index()
        received_columns = rewards_df.columns.values.tolist()
        received_columns.sort()

        expected_columns.sort()

        assert (expected_columns == received_columns), f"Granularity: {granularity} expected_columns: " \
                                                       f"{expected_columns} received_columns: {received_columns}"


    @pytest.mark.parametrize('is_testing', [True, False])
    @pytest.mark.parametrize('granularity', ['tournament', 'tournament_stage', 'match', 'innings'])
    def test_get_error_measures(self, perfect_simulator, is_testing, granularity):

        prepare_for_tests(perfect_simulator.data_selection, is_testing)

        rewards_df = perfect_simulator.get_simulation_evaluation_metrics_by_granularity(is_testing, granularity)

        error_df = perfect_simulator.get_error_measures(is_testing, rewards_df, granularity)

        columns_to_compare = ['batting_rewards', 'bowling_rewards', 'fielding_rewards', 'total_rewards']

        for column in columns_to_compare:
            assert error_df[f'{column}_mean_absolute_error'].unique() == 0.0
            assert error_df[f'{column}_mean_absolute_percentage_error'].unique() == 0.0
