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

