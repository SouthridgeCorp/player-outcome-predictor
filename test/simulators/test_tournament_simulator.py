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
            tournament_simulator.validate_and_setup()


@pytest.mark.parametrize(
    'test_case',
    get_test_cases('app_config', 'TestTournamentSimulatorValidation'),
    scope='class'
)
class TestTournamentSimulator:
    def test_tournament_simulator_validation(self, tournament_simulator):
        try:
            tournament_simulator.validate_and_setup()
        except ValueError as exc:
            assert False, f"Tournament Simulator validation threw an error {exc}"

        assert not tournament_simulator.source_matches_df['match_key'].isna().unique()
        assert not tournament_simulator.source_playing_xi_df['match_key'].isna().unique()
        assert ((tournament_simulator.source_playing_xi_df['match_key'] != 0).all())

