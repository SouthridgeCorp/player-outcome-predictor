from test.conftest import get_test_cases
import pytest

@pytest.mark.parametrize(
    'test_case',
    get_test_cases('app_config', 'TestRewardsConfiguration'),
    scope='class'
)
class TestRewardsConfiguration:

    def test_get_bowling_outcomes_by_ball_and_innings(self, perfect_simulator):

        df = perfect_simulator.get_bowling_outcomes_by_ball_and_innings()
        print("Hello")