import pytest
from test.conftest import get_test_cases
from simulators.perfect_simulator import PerfectSimulator
from test.data_selection.conftest import prepare_tests, setup_training_and_testing_windows
from simulators.utils.predictive_utils import PredictiveUtils
import pandas as pd
from utils.app_utils import show_stats


@pytest.mark.parametrize(
    'test_case',
    get_test_cases('app_config', 'TestPredictiveSimulator'),
    scope='class'
)
class TestPredictiveSimulator:

    def test_bowling_probability_distribution(self, predictive_simulator):
        utils = predictive_simulator.predictive_utils
        utils.setup(False)

        for key in utils.bowling_probabilities.probability_map.keys():
            a = utils.bowling_probabilities.probability_map[key]
            assert sum(a) > 0.9999999

    def test_generate_scenario(self, predictive_simulator, setup_and_teardown):
        prepare_tests(predictive_simulator.data_selection, True)

        test_case, config_instance = setup_and_teardown
        number_of_scenarios = config_instance.get_predictive_simulator_info()

        matches_df = predictive_simulator.data_selection.get_selected_matches(True)
        predictive_simulator.generate_scenario()
        simulated_matches_df = predictive_simulator.simulated_matches_df

        assert len(simulated_matches_df.index) == len(matches_df.index) * number_of_scenarios
        assert simulated_matches_df['toss_winner'].notna().unique().tolist() == [True]

        number_of_fields = len(simulated_matches_df[simulated_matches_df['toss_decision'] == 'field'])
        number_of_bats = len(simulated_matches_df[simulated_matches_df['toss_decision'] == 'bat'])

        assert number_of_fields > 0
        assert number_of_bats > 0
        fielding_ratio = number_of_fields / (number_of_bats + number_of_fields)
        assert fielding_ratio > 0.6
        assert (number_of_bats + number_of_fields) == len(simulated_matches_df.index)

        for index, row in simulated_matches_df.iterrows():
            assert row['toss_winner'] in [row['team1'], row['team2']]
            if row['toss_decision'] == 'bat':
                assert row['batting_team'] == row['toss_winner']
                assert row['bowling_team'] == row['toss_loser']
            else:
                assert row['bowling_team'] == row['toss_winner']
                assert row['batting_team'] == row['toss_loser']

        simulated_innings_df = predictive_simulator.simulated_innings_df

        assert simulated_innings_df[simulated_innings_df['venue'].isna()].empty
        assert simulated_innings_df[simulated_innings_df['bowler'].isna()].empty
        assert simulated_innings_df[simulated_innings_df['batter'].isna()].empty
        assert simulated_innings_df[simulated_innings_df['non_striker'].isna()].empty
        playing_xi_df = predictive_simulator.data_selection.get_playing_xi_for_selected_matches(True)

        assert len(simulated_innings_df[simulated_innings_df['player_dismissed']
                                        == simulated_innings_df['non_striker']].index) > 0

        for (match_key, inning, scenario), innings_df in simulated_innings_df.\
                groupby(['match_key', 'inning', 'scenario_number']):
            batting_team = innings_df['batting_team'].unique().tolist()[0]
            bowling_team = innings_df['bowling_team'].unique().tolist()[0]
            playing_xi = playing_xi_df.query(f'match_key == {match_key} and '
                                            f'team == "{batting_team}"')['player_key'].to_list()
            playing_xi.append('non_frequent_player')
            batters = innings_df['batter'].unique().tolist()
            non_strikers = innings_df['non_striker'].unique().tolist()
            for item in batters:
                assert item in playing_xi, f"Missing batter: {item}"
            for item in non_strikers:
                assert item in playing_xi, f"Missing non striker: {item}"
            assert all(innings_df.query("bowler != 'non_frequent_player'").reset_index()
                       .groupby(['bowler']).nunique()['over'] <= 4)

            assert innings_df.iloc[-1]['previous_number_of_wickets'] + innings_df.iloc[-1]['is_wicket'] <= 10

            if len(innings_df.index) < 20 * 6:
                if innings_df.iloc[-1]['previous_number_of_wickets'] + innings_df.iloc[-1]['is_wicket'] != 10:
                    assert innings_df.iloc[-1]['previous_total'] + innings_df.iloc[-1]['batter_runs'] \
                           + innings_df.iloc[-1]['extras'] >= innings_df.iloc[-1]['target_runs']

            mask = innings_df['is_wicket'] == 1
            assert 'nan' not in innings_df.loc[mask]['dismissal_kind'].unique().tolist()
            assert innings_df.loc[~mask]['dismissal_kind'].unique().tolist() == ['nan']
            assert 'nan' not in innings_df.loc[mask]['player_dismissed'].unique().tolist()
            assert innings_df.loc[~mask]['player_dismissed'].unique().tolist() == ['nan']

            mask = innings_df['dismissal_kind'].isin(['caught', 'run out', 'stumped'])

            assert 'nan' not in innings_df.loc[mask]['fielder'].unique().tolist()
            assert innings_df.loc[~mask]['fielder'].unique().tolist() == ['nan']

            bowling_playing_xi = playing_xi_df.query(f'match_key == {match_key} and '
                                             f'team == "{bowling_team}"')['player_key'].to_list()
            bowling_playing_xi.append('non_frequent_player')
            fielders = innings_df.loc[mask]['fielder'].unique().tolist()
            for item in fielders:
                assert item in bowling_playing_xi, f"Missing fielder: {item}"

            bowlers = innings_df.loc[mask]['bowler'].unique().tolist()
            for item in bowlers:
                assert item in bowling_playing_xi, f"Missing bowler: {item}"

            mask = innings_df['player_dismissed'] == innings_df['non_striker']
            if not innings_df[mask].empty:
                if innings_df.loc[mask]['dismissal_kind'].unique().tolist() != ["run out"]:
                    mask = mask & (innings_df['dismissal_kind'] != 'run out')
                    assert innings_df.loc[mask]['player_dismissed'].unique().tolist() == ['non_frequent_player']

            innings_total = innings_df.iloc[-1]['previous_total'] + innings_df.iloc[-1]['batter_runs']\
                            + innings_df.iloc[-1]['extras']
            innings_wickets = innings_df.iloc[-1]['previous_number_of_wickets'] + innings_df.iloc[-1]['is_wicket']

            assert innings_wickets <= 10

            calculated_total = 0
            calculated_num_wickets = 0

            for index, row in innings_df.iterrows():
                calculated_total += row['batter_runs'] + row['extras']
                calculated_num_wickets += row['is_wicket']

            assert calculated_num_wickets == innings_wickets
            assert innings_total == calculated_total

            number_of_overs = innings_df.reset_index()['over'].max()
            for i in range(0, number_of_overs-1):
                bowler1 = innings_df.query(f"over == {i} and ball == 1").iloc[0]["bowler"]
                bowler2 = innings_df.query(f"over == {i+1} and ball == 1").iloc[0]["bowler"]
                assert bowler1 != bowler2 if bowler1 != 'non_frequent_player' else True

            if inning == 2:
                winner = predictive_simulator.simulated_matches_df.loc[(scenario, match_key)]['winner']
                batting_runs = innings_df.iloc[-1]['total_runs'] + innings_df.iloc[-1]['previous_total']
                target_runs = innings_df.iloc[-1]['target_runs']
                assert winner in [bowling_team, batting_team]
                if winner == bowling_team:
                    assert batting_runs < target_runs
                else:
                    assert batting_runs >= target_runs

    @pytest.mark.parametrize('granularity', ['tournament', 'tournament_stage', 'match', 'innings'])
    def test_get_error_measures_predictive_simulator(self, predictive_simulator, granularity):

        prepare_tests(predictive_simulator.data_selection, True)
        predictive_simulator.generate_scenario()

        perfect_simulator_for_testing = PerfectSimulator(predictive_simulator.data_selection,
                                                         predictive_simulator.rewards_configuration)
        perfect_df = perfect_simulator_for_testing.get_simulation_evaluation_metrics_by_granularity(True, granularity)
        total_errors_df = pd.DataFrame()
        for scenario in range(0, predictive_simulator.number_of_scenarios):
            rewards_df = predictive_simulator.perfect_simulators[scenario]\
                .get_simulation_evaluation_metrics_by_granularity(True, granularity)

            error_df = perfect_simulator_for_testing.get_error_measures(True, rewards_df, granularity, perfect_df)

            columns_to_compare = ['batting_rewards', 'bowling_rewards', 'fielding_rewards', 'total_rewards']

            for column in columns_to_compare:
                mask = error_df[f'{column}_absolute_error'] != abs(error_df[f'{column}_expected']
                                                                   - error_df[f'{column}_received'])
                assert error_df[mask].empty

                mask = (error_df[f'{column}_expected'] != 0) & (error_df[f'{column}_absolute_percentage_error'] != \
                                                                abs(100 * (error_df[f'{column}_expected'] - error_df[
                                                                    f'{column}_received']) \
                                                                    / error_df[f'{column}_expected']))
                assert error_df[mask].empty

                assert error_df.query(f'{column}_absolute_error < 0.0').empty
                assert error_df.query(f'{column}_absolute_percentage_error < 0.0').empty

            error_df['scenario_number'] = scenario
            total_errors_df = pd.concat([total_errors_df, error_df])

        new_error_df = predictive_simulator.get_error_stats(granularity)
        differences = pd.concat([new_error_df.reset_index(), total_errors_df.reset_index()]).drop_duplicates(keep=False)
        assert differences.empty
