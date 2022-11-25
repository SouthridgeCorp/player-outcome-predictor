import pytest
from inferential_models.batter_runs_models import BatterRunsModel
import pymc as pm
import aesara.tensor as at
from test.conftest import get_test_cases
import pymc as pm

@pytest.mark.parametrize(
    'test_case',
    get_test_cases('app_config', 'TestBatterRunsModel'),
    scope='class'
)
class TestBatterRunsModel:

    def test_model_trained(self,batter_runs_model:BatterRunsModel):
        model = batter_runs_model
        session_type = 'training'
        model.initiate_model(session_type)
        model.run_training()
        session_type = 'testing'
        model.initiate_model(session_type)
        testing_stats = model.run_testing()
        assert 'classification_report' in testing_stats
        assert 'confusion_matrix' in testing_stats

    def test_model_inference(self,batter_runs_model):
        model = batter_runs_model
        session_type = 'testing'
        model.initiate_model(session_type)
        test_match_state_df = model.perfect_simulator.get_match_state_by_ball_and_innings(True)
        predicted_batter_runs_outcomes = model.get_batter_runs_given_match_state(test_match_state_df)

        assert predicted_batter_runs_outcomes.shape[0] == test_match_state_df.shape[0]
        assert 'batter_runs' in predicted_batter_runs_outcomes.columns

