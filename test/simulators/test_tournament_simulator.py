from test.conftest import get_test_cases
from test.data_selection.conftest import setup_training_and_testing

import pytest
from test.data_selection.conftest import prepare_for_tests
import logging

logging.basicConfig()
logging.getLogger().setLevel(logging.DEBUG)

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

        assert not tournament_simulator.source_matches_df['key'].isna().unique()
        assert not tournament_simulator.source_playing_xi_df['match_key'].isna().unique()
        assert ((tournament_simulator.source_playing_xi_df['match_key'] != 0).all())

        match_keys_match = list(tournament_simulator.get_group_stage_matches()['key'].values)
        match_keys_match.sort()

        match_keys_playing_xi = list(tournament_simulator.source_playing_xi_df['match_key'].unique())
        match_keys_playing_xi.sort()

        assert match_keys_match == match_keys_playing_xi

        assert list(tournament_simulator.source_playing_xi_df.groupby('match_key')['player_key'].count().unique()) \
               == [22]


    def test_generate_scenarios(self, tournament_simulator):
        prepare_for_tests(tournament_simulator.data_selection, True)
        all_matches_df = tournament_simulator.generate_scenarios()

        mask = all_matches_df['stage'].isin(['Final', 'Qualifier 1', 'Qualifier 2', 'Eliminator'])
        assert not all(all_matches_df[mask]['team1'].isna())
        assert not all(all_matches_df[mask]['team2'].isna())
        assert all(all_matches_df['team1'] != all_matches_df['team2'])

        q1_mask = all_matches_df['stage'] == 'Qualifier 1'
        q2_mask = all_matches_df['stage'] == 'Qualifier 2'
        final_mask = all_matches_df['stage'] == 'Final'

        assert list(all_matches_df[final_mask]['team1']) == list(all_matches_df[q1_mask]['winner'])
        assert list(all_matches_df[final_mask]['team2']) == list(all_matches_df[q2_mask]['winner'])

        for tournament_scenario, matches_df in all_matches_df.groupby('tournament_scenario'):
            group_matches_df = matches_df[~matches_df['stage'].isin(tournament_simulator.non_group_stages)]
            top_4_df = group_matches_df.groupby('winner').count()['key'].nlargest(4)
            q1_mask = matches_df['stage'] == 'Qualifier 1'
            q2_mask = matches_df['stage'] == 'Qualifier 2'
            elim_mask = matches_df['stage'] == 'Eliminator'

            assert list(matches_df[q1_mask]['team1']) == [top_4_df.index[0]]
            assert list(matches_df[q1_mask]['team2']) == [top_4_df.index[1]]
            assert list(matches_df[elim_mask]['team1']) == [top_4_df.index[2]]
            assert list(matches_df[elim_mask]['team2']) == [top_4_df.index[3]]

            assert list(matches_df[q2_mask]['team1']) == list(matches_df[q1_mask]['loser'])
            assert list(matches_df[q2_mask]['team2']) == list(matches_df[elim_mask]['winner'])

            print('Hello')