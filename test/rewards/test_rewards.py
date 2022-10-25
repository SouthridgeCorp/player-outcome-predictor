import pytest
from test.conftest import get_test_cases


@pytest.mark.parametrize(
    'test_case',
    get_test_cases('utils/config_utils','TestRewards'),
    scope='class'
)
def test_rewards_generation(setup_and_teardown):
    test_case, config_instance = setup_and_teardown

    print(test_case)