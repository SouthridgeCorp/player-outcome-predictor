import pytest
from test.conftest import get_test_cases
from test.data_selection.conftest import prepare_for_tests, setup_training_and_testing
import pandas as pd


@pytest.mark.parametrize(
    'test_case',
    get_test_cases('app_config', 'TestPredictiveSimulator'),
    scope='class'
)
class TestPredictiveSimulator:

    def test_generate_scenario(self, predictive_simulator, setup_and_teardown):
        prepare_for_tests(predictive_simulator.data_selection, True)

        test_case, config_instance = setup_and_teardown
        number_of_scenarios = config_instance.get_predictive_simulator_info()

        matches_df = predictive_simulator.data_selection.get_selected_matches(True)
        predictive_simulator.generate_scenario()
        #predictive_simulator.generate_scenario()
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





"""
    @pytest.mark.parametrize('sequence_number', [1])
    def test_predict_selected_matches(self, predictive_simulator, sequence_number):
        prepare_for_tests(predictive_simulator.data_selection, True)

        all_matches_df = predictive_simulator.data_selection.get_selected_matches(True)
        predictive_simulator.predictive_utils.setup_with_matches(all_matches_df)
        all_matches_df.set_index('key', inplace=True)


        matches_df = predictive_simulator.predict_selected_matches(sequence_number, all_matches_df)
        assert list(matches_df[matches_df['predicted_toss_winner'] == matches_df['team1']]
                    ['predicted_team_1_won_toss'].unique()) == [1]
        assert list(matches_df[matches_df['predicted_toss_winner'] != matches_df['team1']]
                    ['predicted_team_1_won_toss'].unique()) == [0]
        assert matches_df['predicted_toss_winner'].notna().unique().tolist() == [True]

"""
