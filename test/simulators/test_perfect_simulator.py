from test.conftest import get_test_cases
import pytest
from test.data_selection.conftest import prepare_tests, setup_training_and_testing_windows
import pandas as pd
from data_selection.data_selection import DataSelectionType
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
                if no_ball >= 1:
                    if batter_runs > 0:
                        outcome_index += f"{batter_runs}-b,"
                    if extras > 0:
                        outcome_index += f"{extras}-"
                    outcome_index += f"nb"
                elif wides >= 1:
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
        prepare_tests(perfect_simulator.data_selection, is_testing)
        df = perfect_simulator.get_bowling_outcomes_by_ball_and_innings(is_testing)

        for index, row in df.iterrows():
            expected_bowling_outcome = TestPerfectSimulator.bowling_outcome(row)
            received_bowling_outcome = row['bowling_outcome_index']
            assert received_bowling_outcome == expected_bowling_outcome, f"Outcomes don't match for {index}. " \
                                                                         f"Exepcted: {expected_bowling_outcome} but " \
                                                                         f"Received: {received_bowling_outcome}"

    @pytest.mark.parametrize('is_testing', [True, False])
    def test_get_match_state_by_ball_and_innings(self, perfect_simulator, setup_and_teardown, is_testing):
        setup_training_and_testing_windows(perfect_simulator.data_selection)

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
        prepare_tests(perfect_simulator.data_selection, is_testing)

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
        prepare_tests(perfect_simulator.data_selection, is_testing)

        df = perfect_simulator.get_fielding_outcomes_by_ball_and_innings(is_testing)

        expected_df = perfect_simulator.get_bowling_outcomes_by_ball_and_innings(is_testing)
        innings_df = perfect_simulator.data_selection.get_innings_for_selected_matches(is_testing)
        index_columns = ['match_key', 'inning', 'over', 'ball']
        innings_df.set_index(index_columns, inplace=True)

        TestPerfectSimulator.bowling_to_fielding_outcomes_converter(expected_df, innings_df)

        df = pd.merge(df, expected_df['fielding_outcome_index_expected'], left_index=True, right_index=True)

        assert df['fielding_outcome_index'].equals(df['fielding_outcome_index_expected'])

    def get_outcomes_for_testing(self, simulator, is_testing):
        innings_df = simulator.data_selection.get_innings_for_selected_matches(is_testing).copy()
        matches_df = simulator.data_selection.get_selected_matches(is_testing)

        innings_df = pd.merge(innings_df, matches_df[['key', 'tournament_key', 'stage']],
                              left_on='match_key', right_on='key')

        outcomes_list = []
        fielder_list = []
        non_striker_list = []
        # Calculate the batting strike rate
        for g, g_df in innings_df.groupby(['match_key', 'inning', 'batting_team', 'batter']):
            total_balls_bowled = len(g_df) - g_df['wides'].count() - g_df['noballs'].count()
            total_runs_made = g_df['batter_runs'].sum()
            total_runs = g_df['total_runs'].sum()
            batting_strike_rate = 100 * total_runs_made / total_balls_bowled
            outcomes_list.append({'match_key': g[0], 'inning': g[1], 'team': g[2],
                                  'player_key': g[3],
                                  'total_balls': total_balls_bowled, 'batting_total_runs': total_runs_made,
                                  'batting_total_runs_with_extras': total_runs,
                                  'strike_rate': batting_strike_rate})

        for g, g_df in innings_df.groupby(['match_key', 'inning', 'batting_team', 'non_striker']):
            non_striker_count = g_df['non_striker'].count()
            non_striker_list.append({'match_key': g[0], 'inning': g[1], 'team': g[2],
                                  'player_key': g[3], 'non_striker_count': non_striker_count})

        # Calculate the bowling econ rate & number of wickets
        mask = innings_df['dismissal_kind'] == 'run out'
        innings_df['is_runout'] = 0
        innings_df.loc[mask, 'is_runout'] = 1
        for g, g_df in innings_df.groupby(['match_key', 'inning', 'bowling_team', 'bowler']):
            number_of_deliveries = g_df['bowler'].count() - g_df['wides'].count() - g_df['noballs'].count()
            total_runs_made = g_df['total_runs'].sum() - g_df['byes'].sum() - g_df['legbyes'].sum()
            number_of_wickets = g_df['is_wicket'].sum()
            bowling_total_runs_with_extras = g_df['total_runs'].sum()

            # Runouts are not credited to the bowler
            number_of_runouts = len(g_df[g_df['dismissal_kind'] == 'run out'])
            number_of_wickets -= number_of_runouts
            economy_rate = total_runs_made / number_of_deliveries


            outcomes_list.append({'match_key': g[0], 'inning': g[1], 'team': g[2],
                                  'player_key': g[3],
                                  'number_of_bowled_deliveries': number_of_deliveries, 'total_runs': total_runs_made,
                                  'bowling_total_runs_with_extras': bowling_total_runs_with_extras,
                                  'wickets_taken': number_of_wickets, 'economy_rate': economy_rate})

        for g, g_df in innings_df.groupby(['match_key', 'inning', 'bowling_team', 'fielder']):
            number_of_fielding_events = g_df['fielder'].count()
            fielder_list.append({'match_key': g[0], 'inning': g[1], 'team': g[2],
                                  'player_key': g[3], 'number_of_fielding_events': number_of_fielding_events})

        outcomes_df = pd.DataFrame(data=outcomes_list)
        non_striker_df = pd.DataFrame(data=non_striker_list)
        fielder_df = pd.DataFrame(data=fielder_list)
        index_columns = ['match_key', 'inning', 'team', 'player_key']

        outcomes_df.set_index(index_columns, inplace=True, verify_integrity=True)
        fielder_df.set_index(index_columns, inplace=True, verify_integrity=True)
        non_striker_df.set_index(index_columns, inplace=True, verify_integrity=True)

        outcomes_df = pd.merge(outcomes_df, non_striker_df['non_striker_count'],
                               left_index=True, right_index=True, how='outer')
        outcomes_df = pd.merge(outcomes_df, fielder_df['number_of_fielding_events'],
                               left_index=True, right_index=True, how='outer')

        outcomes_df = outcomes_df.reset_index()
        outcomes_df = pd.merge(outcomes_df, matches_df[['key', 'tournament_key', 'stage']],
                               left_on='match_key', right_on='key')
        outcomes_df.drop('key', axis=1, inplace=True)

        outcomes_df.set_index(index_columns, inplace=True, verify_integrity=True)

        outcomes_df = outcomes_df.sort_values(index_columns)
        return outcomes_df

    @pytest.mark.parametrize('is_testing', [True, False])
    def test_get_outcomes_by_ball_and_innings(self, perfect_simulator, is_testing):
        prepare_tests(perfect_simulator.data_selection, is_testing)

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
        prepare_tests(perfect_simulator.data_selection, is_testing)

        df = perfect_simulator.get_outcomes_by_player_and_innings(is_testing)

        expected_columns = ['batting_total_runs', 'batting_total_runs_with_extras', 'bowling_total_runs_with_extras',
                            'economy_rate', 'non_striker_count', 'number_of_bowled_deliveries',
                            'number_of_fielding_events', 'stage', 'strike_rate', 'total_balls', 'total_runs',
                            'tournament_key', 'wickets_taken']

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

        outcomes_df = self.get_outcomes_for_testing(perfect_simulator, is_testing)
        differences = pd.concat([outcomes_df, df]).drop_duplicates(keep=False)
        assert differences.empty

    def get_outcomes_by_team_and_innings_for_testing(self, simulator, is_testing):
        # Calculate all the fields for player get_outcome_labels
        player_outcomes = simulator.get_outcomes_by_player_and_innings(is_testing)
        innings_outcomes_list = []
        for g, g_df in player_outcomes.groupby(['match_key', 'inning', 'team']):
            total_runs = g_df['bowling_total_runs_with_extras'].sum()
            total_balls = g_df['total_balls'].sum()
            batting_total_runs = g_df['batting_total_runs_with_extras'].sum()
            inning_number_of_bowled_deliveries = g_df['number_of_bowled_deliveries'].sum()
            economy_rate = (total_runs / inning_number_of_bowled_deliveries) if \
                inning_number_of_bowled_deliveries != 0 else 0
            strike_rate = (100 * batting_total_runs / total_balls) if total_balls != 0 else 0
            innings_outcomes_list.append({'match_key': g[0], 'inning': g[1], 'team': g[2],
                                          'inning_batting_total_runs': batting_total_runs,
                                          'inning_total_balls': total_balls,
                                          'inning_total_runs': total_runs,
                                          'inning_number_of_bowled_deliveries': inning_number_of_bowled_deliveries,
                                          'inning_strike_rate': strike_rate,
                                          'inning_economy_rate': economy_rate})

        innings_outcomes_df = pd.DataFrame(data=innings_outcomes_list)
        index_columns = ['match_key', 'inning', 'team']
        innings_outcomes_df.set_index(index_columns, inplace=True, verify_integrity=True)
        innings_outcomes_df = innings_outcomes_df.sort_values(index_columns)
        return innings_outcomes_df

    @pytest.mark.parametrize('is_testing', [True, False])
    def test_get_outcomes_by_team_and_innings(self, perfect_simulator, is_testing):
        prepare_tests(perfect_simulator.data_selection, is_testing)

        df = perfect_simulator.get_outcomes_by_team_and_innings(is_testing)

        expected_columns = ['inning_batting_total_runs', 'inning_economy_rate', 'inning_number_of_bowled_deliveries',
                            'inning_strike_rate', 'inning_total_balls', 'inning_total_runs']
        expected_columns.sort()
        received_columns = df.columns.values.tolist()
        received_columns.sort()

        assert expected_columns == received_columns, f"Expected: {expected_columns}\nReceived: {received_columns}"
        expected_outcomes_df = self.get_outcomes_by_team_and_innings_for_testing(perfect_simulator, is_testing)
        pd.testing.assert_frame_equal(df, expected_outcomes_df)


    def get_expected_batting_rewards(self, batting_outcome, row):
        expected_base_reward = 0
        extras = row['extras']

        if batting_outcome == '0' or (batting_outcome == 'E'):
            expected_base_reward = -1
            if (extras > 0) and (expected_base_reward < 0):
                expected_base_reward = 0
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
            expected_base_reward = -5
            if extras == 0:
                expected_base_reward = -6
        elif batting_outcome.endswith('W'):
            runs = batting_outcome.split(",")[0]
            expected_base_reward = -5 + self.get_expected_batting_rewards(runs, row)

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

        if row['byes'] > 0 or row['legbyes'] > 0:
            reward = 0

        wides = row["wides"]
        no_ball = row["noballs"]
        if no_ball >= 1:
            reward += -3
        if wides >= 1:
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
        prepare_tests(perfect_simulator.data_selection, is_testing)

        base_rewards_df, bonus_penalty_df = perfect_simulator.get_rewards_components(is_testing, generate_labels=True)

        for index, row in base_rewards_df.iterrows():
            expected_batting_reward = self.get_expected_batting_rewards(row['batter_outcome_index'], row)
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
            if pd.isna(row['bowling_bonus']):
                assert row['bowling_rewards'] == 0.0
            else:
                assert row['bowling_rewards'] == row['bowling_base_rewards'] + row['bowling_bonus_wickets'] \
                       + row['bowling_bonus']

            if pd.isna(row['batting_bonus']):
                assert row['batting_rewards'] == 0.0
            else:
                assert row['batting_rewards'] == row['batter_base_rewards'] + row['batting_bonus']

        matches_df = perfect_simulator.data_selection.get_innings_for_selected_matches(is_testing)
        batters = list(matches_df['batter'].unique())
        bowlers = list(matches_df['bowler'].unique())
        fielders = list(matches_df['fielder'].dropna().unique())
        non_strikers = list(matches_df['non_striker'].unique())

        players = batters + bowlers + fielders + non_strikers
        unique_players = list(set(players))
        unique_players.sort()

        rewards_players = list(bonus_penalty_df.reset_index()['player_key'].unique())
        rewards_players.sort()

        assert unique_players == rewards_players



    @pytest.mark.parametrize('is_testing', [True, False])
    @pytest.mark.parametrize('granularity, expected_columns',
                             [('tournament', ['name', 'number_of_matches', 'player_key', 'tournament_key',
                                              'bowling_rewards', 'batting_rewards', 'fielding_rewards',
                                              'total_rewards']),
                              ('tournament_stage', ['name', 'number_of_matches', 'player_key', 'tournament_key',
                                                    'stage', 'bowling_rewards', 'batting_rewards', 'fielding_rewards',
                                                    'total_rewards']),
                              ('match', ['name', 'number_of_matches','player_key', 'tournament_key', 'stage',
                                         'match_key', 'bowling_rewards', 'batting_rewards', 'fielding_rewards',
                                         'total_rewards']),
                              ('innings', ['name', 'number_of_matches', 'player_key', 'tournament_key', 'stage',
                                           'match_key', 'inning', 'bowling_rewards', 'batting_rewards',
                                           'fielding_rewards', 'total_rewards'])])
    def test_get_simulation_evaluation_metrics_by_granularity(self, perfect_simulator, is_testing, granularity,
                                                              expected_columns):

        prepare_tests(perfect_simulator.data_selection, is_testing)
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

        prepare_tests(perfect_simulator.data_selection, is_testing)

        rewards_df = perfect_simulator.get_simulation_evaluation_metrics_by_granularity(is_testing, granularity)

        error_df = perfect_simulator.get_error_measures(is_testing, rewards_df, granularity)

        columns_to_compare = ['batting_rewards', 'bowling_rewards', 'fielding_rewards', 'total_rewards']

        for column in columns_to_compare:
            assert error_df[f'{column}_absolute_error'].unique() == 0.0
            assert error_df[f'{column}_absolute_percentage_error'].unique() == 0.0

    def test_get_match_state_by_balls_for_training(self, perfect_simulator):

        setup_training_and_testing_windows(perfect_simulator.data_selection)
        unqualified_train_match_state_df = perfect_simulator.get_match_state_by_ball_and_innings(False, False)
        unqualified_train_bowling_outcomes_df = perfect_simulator.get_bowling_outcomes_by_ball_and_innings(False)
        test_season_matches = perfect_simulator.data_selection.get_selected_matches(True)
        test_season_innings = perfect_simulator.data_selection.get_innings_for_selected_matches(True)

        test_season_venues = test_season_matches.venue.unique().tolist()
        test_season_batters = test_season_innings.batter.unique().tolist()
        test_season_bowlers = test_season_innings.bowler.unique().tolist()

        is_test_season_venue = unqualified_train_match_state_df.venue.isin(test_season_venues)
        is_test_season_batter = unqualified_train_match_state_df.batter.isin(test_season_batters)
        is_test_season_bowler = unqualified_train_match_state_df.bowler.isin(test_season_bowlers)

        selection_options = {
            DataSelectionType.OR_SELECTION: is_test_season_venue | is_test_season_batter | is_test_season_bowler,
            DataSelectionType.AND_SELECTION: is_test_season_venue & is_test_season_batter & is_test_season_bowler
        }

        perfect_simulator.data_selection.set_selection_type(DataSelectionType.AND_SELECTION)
        and_match_state, and_bowling_outcomes_df, and_stats = perfect_simulator.get_match_state_by_balls_for_training(
            one_hot_encoding=False)

        assert len(unqualified_train_match_state_df.index) > len(and_match_state.index)
        assert len(unqualified_train_bowling_outcomes_df.index) > len(and_bowling_outcomes_df.index)
        assert and_match_state.loc[~selection_options[DataSelectionType.AND_SELECTION]].empty

        perfect_simulator.data_selection.set_selection_type(DataSelectionType.OR_SELECTION)
        or_match_state, or_bowling_outcomes_df, or_stats = perfect_simulator.get_match_state_by_balls_for_training(
            one_hot_encoding=False)

        assert len(unqualified_train_match_state_df.index) > len(or_match_state.index)
        assert len(unqualified_train_bowling_outcomes_df.index) > len(or_bowling_outcomes_df.index)
        assert or_match_state.loc[~selection_options[DataSelectionType.OR_SELECTION]].empty

        assert len(or_match_state.index) > len(and_match_state.index)

