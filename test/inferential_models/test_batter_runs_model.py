import pytest
from inferential_models.batter_runs_models import BatterRunsModel
import pymc as pm
import aesara.tensor as at
from test.conftest import get_test_cases
from test.data_selection.conftest import setup_training_and_testing, prepare_for_tests
import pymc as pm

@pytest.mark.parametrize(
    'test_case',
    get_test_cases('app_config', 'TestBatterRunsModel'),
    scope='class'
)
class TestBatterRunsModel:

    def test_model_instantiated(self,batter_runs_model):
        model = batter_runs_model
        prepare_for_tests(model.perfect_simulator.data_selection, True)
        test_match_state_df = model.perfect_simulator.get_match_state_by_ball_and_innings(True).iloc[:280]
        predicted_batter_runs_outcomes = model.get_batter_runs_given_match_state(test_match_state_df)

        assert predicted_batter_runs_outcomes.shape[0] == test_match_state_df.shape[0]
        assert predicted_batter_runs_outcomes.columns.to_list() == ['batter_runs','probability']

