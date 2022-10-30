from test.conftest import get_test_cases
import pytest
from test.data_selection.conftest import prepare_for_tests
import pandas as pd


@pytest.mark.parametrize(
    'test_case',
    get_test_cases('app_config', 'TestPerfectSimulator'),
    scope='class'
)
class TestRewardsConfiguration:


    @pytest.mark.parametrize('is_testing', [True, False])
    def test_get_bowling_outcomes_by_ball_and_innings(self, perfect_simulator, setup_and_teardown, is_testing):
        prepare_for_tests(perfect_simulator.data_selection, is_testing)
        df = perfect_simulator.get_bowling_outcomes_by_ball_and_innings(is_testing)

        test_case, config_instance = setup_and_teardown
        baseline_file = test_case['baseline_file']
        expected_df = pd.read_csv(baseline_file)
        expected_df = expected_df.astype(str)
        df = df.astype(str)

        expected_columns = ["match_key", "inning", "over", "ball", "bowler", "bowling_outcome_index"]

        for column in expected_columns:
            pd.testing.assert_series_equal(df[column], expected_df[column], check_index=False)
