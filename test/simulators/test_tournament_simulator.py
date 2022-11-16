from test.conftest import get_test_cases
from test.data_selection.conftest import setup_training_and_testing

import pytest

@pytest.mark.parametrize(
    'test_case',
    get_test_cases('app_config', 'TestTournamentSimulatorMissingDetails'),
    scope='class'
)
class TestTournamentSimulatorMissingDetails:
    def test_tournament_simulator_validation(self, tournament_simulator):
        with pytest.raises(ValueError) as e_info:
            tournament_simulator.validate_source_files()


@pytest.mark.parametrize(
    'test_case',
    get_test_cases('app_config', 'TestTournamentSimulatorValidation'),
    scope='class'
)
class TestTournamentSimulator:
    def test_tournament_simulator_validation(self, tournament_simulator):
        try:
            tournament_simulator.validate_source_files()
        except ValueError as exc:
            assert False, f"Tournament Simulator validation threw an error {exc}"

