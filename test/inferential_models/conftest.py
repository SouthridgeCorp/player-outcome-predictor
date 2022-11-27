import pytest
import scipy.stats as sps
import numpy as np
import pandas as pd
from scipy.special import softmax
from collections import Counter
import datetime

from data_selection.data_selection import DataSelection, DataSelectionType
from historical_data.singleton import Helper
from inferential_models.batter_runs_models import BatterRunsModel
from rewards_configuration.rewards_configuration import RewardsConfiguration
from simulators.perfect_simulator import PerfectSimulator
from test.data_selection.conftest import prepare_tests


def get_toss_winning_team(row):
    if row['toss_won_by_team1'] == 1:
        return row['team1']
    else:
        return row['team2']


def get_toss_losing_team(row):
    if row['toss_won_by_team1'] == 1:
        return row['team2']
    else:
        return row['team1']


def get_innings1_bowling_team(row):
    if row['toss_winning_team_bowls'] == 1:
        return row['toss_winning_team']
    else:
        return row['toss_losing_team']


def get_innings1_batting_team(row):
    if row['toss_winning_team_bowls'] == 1:
        return row['toss_losing_team']
    else:
        return row['toss_winning_team']


def get_innings2_bowling_team(row):
    if row['toss_winning_team_bowls'] == 1:
        return row['toss_losing_team']
    else:
        return row['toss_winning_team']


def get_innings2_batting_team(row):
    if row['toss_winning_team_bowls'] == 1:
        return row['toss_winning_team']
    else:
        return row['toss_losing_team']

@pytest.fixture
def simulate_match_data():
    num_teams = 10
    num_matches = num_teams * (num_teams - 1)
    num_venues = 5
    num_players = num_teams * 11 + 1
    toss_won_by_team1_probability = sps.bernoulli(p=0.5)
    toss_won_by_team1_outcomes_by_match = toss_won_by_team1_probability.rvs(num_matches)
    toss_winning_team_bowls_probability = sps.bernoulli(p=0.8)
    toss_winning_team_bowls_outcomes = toss_winning_team_bowls_probability.rvs(num_matches)
    teams = np.arange(0, num_teams)
    team_combinations = np.array(np.meshgrid(teams, teams)).T.reshape(-1, 2)
    team_combinations_df = pd.DataFrame(team_combinations,
                                        columns=['team1', 'team2'])
    team_combinations_df = team_combinations_df.loc[
        team_combinations_df.team1 != team_combinations_df.team2].reset_index(drop=True)
    matches_df = team_combinations_df.copy()
    matches_df['match_key'] = np.arange(0, num_matches)
    matches_df['toss_won_by_team1'] = toss_won_by_team1_outcomes_by_match
    matches_df['toss_winning_team'] = matches_df.apply(get_toss_winning_team,
                                                       axis=1)
    matches_df['toss_losing_team'] = matches_df.apply(get_toss_losing_team,
                                                      axis=1)
    matches_df['toss_winning_team_bowls'] = toss_winning_team_bowls_outcomes
    matches_df['innings1_batting_team'] = matches_df.apply(get_innings1_batting_team,
                                                           axis=1)
    matches_df['innings1_bowling_team'] = matches_df.apply(get_innings1_bowling_team,
                                                           axis=1)
    matches_df['innings2_batting_team'] = matches_df.apply(get_innings2_batting_team,
                                                           axis=1)
    matches_df['innings2_bowling_team'] = matches_df.apply(get_innings2_bowling_team,
                                                           axis=1)
    players_by_team = np.array([[f'team{team_id}_player{player_id}'
                                 for player_id in range(12)]
                                for team_id in range(num_teams)])
    player_id_index, player_id = pd.Series(players_by_team.ravel()).factorize()
    player2idx = pd.DataFrame({'player_id': player_id_index}, index=player_id)
    p_player_bowls_over = np.array([sps.dirichlet.rvs(np.ones(players_by_team.shape[1]), size=21).T
                                    for team in range(num_teams)])
    p_batsman_at_position = np.array([sps.dirichlet.rvs(np.ones(players_by_team.shape[1]), size=11)
                                      for team in range(num_teams)])
    bowling_outcomes_index = pd.DataFrame({
        'bowling_outcomes_index': ['0', '1-b', '1-oe', '1-nb', '1-w', '2-b', '2-oe', '2-nb', '2-w', '3-b', '3-oe',
                                   '3-nb', '3-w', '4-b', '4-oe', '4-nb', '4-w', '5-b', '5-oe', '5-nb', '5-w', '6-b',
                                   '6-oe', '6-nb', '6-w', 'W-b', 'W-bc', 'W-bs', 'W-dro',
                                   'W-idro', 'W-others'],
        'runs_scored': [0, 1, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 3, 4, 4, 4, 4, 5, 5, 5, 5, 6, 6, 6, 6, 0, 0, 0, 0, 0, 0],
        'batter_switched': [1, 1, 1, 0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0,
                            0],
        'is_legal': [1, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 1, 1, 1, 1]
    })
    bowling_outcomes_index['alpha_for_bowling_outcome_index'] = sps.norm(0, 1).rvs(size=bowling_outcomes_index.shape[0])
    beta_by_player_and_bowling_outcome = np.array([[sps.norm(0, 1).rvs(size=bowling_outcomes_index.shape[0])
                                                    for player in range(12)]
                                                   for team in range(num_teams)])
    #Match simulation
    bowling_outcome_by_ball_and_innings_list = []
    match_state_by_ball_and_innings_list = []
    match_stats_list = []

    for match_key, match_df in matches_df.groupby('match_key'):
        match_stats = {}
        for innings in range(2):
            bowler_overs_bowled = Counter()
            total_balls_bowled = 0
            wickets_lost = 0
            current_score = 0
            batters_dismissed = set()
            bowling_team_id = match_df[f'innings{innings + 1}_bowling_team'].iloc[0]
            batting_team_id = match_df[f'innings{innings + 1}_batting_team'].iloc[0]
            onstrike_batter_rv = sps.multinomial(1, p_batsman_at_position[batting_team_id, 0, :]).rvs(1)[0]
            onstrike_batter_id = np.where(onstrike_batter_rv == 1)[0][0]
            offstrike_batter_id = onstrike_batter_id
            while offstrike_batter_id == onstrike_batter_id:
                offstrike_batter_rv = sps.multinomial(1, p_batsman_at_position[batting_team_id, 1, :]).rvs(1)[0]
                offstrike_batter_id = np.where(offstrike_batter_rv == 1)[0][0]
            onstrike_batter_name = f"team{batting_team_id}_player{onstrike_batter_id}"
            onstrike_batter_player_idx = player2idx.loc[onstrike_batter_name]['player_id']
            offstrike_batter_name = f"team{batting_team_id}_player{offstrike_batter_id}"
            offstrike_batter_player_idx = player2idx.loc[offstrike_batter_name]['player_id']
            for over in range(20):
                selected_bowler_has_overs = False
                while not (selected_bowler_has_overs):
                    selected_bowler_rv = sps.multinomial(1, p_player_bowls_over[bowling_team_id, :, over]).rvs(1)[0]
                    selected_bowler_id = np.where(selected_bowler_rv == 1)[0][0]
                    selected_bowler_name = f"team{bowling_team_id}_player{selected_bowler_id}"
                    selected_bowler_player_idx = player2idx.loc[selected_bowler_name]['player_id']
                    if bowler_overs_bowled[selected_bowler_id] < 4:
                        selected_bowler_has_overs = True
                legal_balls_bowled_in_over = 0
                total_balls_bowled_in_over = 0
                while legal_balls_bowled_in_over < 6:
                    if innings == 0:
                        runs_to_target = -1
                    else:
                        runs_to_target = target - current_score
                    ball_number_in_over = min(6, total_balls_bowled_in_over)
                    match_state_row = {
                        'match_key': match_key,
                        'innings': innings,
                        'over_number': over,
                        'ball_number_in_over': ball_number_in_over,
                        'bowler_id': selected_bowler_player_idx,
                        'batter_id': onstrike_batter_player_idx,
                        'current_score': current_score,
                        'batting_team_id': batting_team_id,
                        'bowling_team_id': bowling_team_id,
                        'wickets_fallen': wickets_lost,
                        'total_balls_bowled': total_balls_bowled,
                        'runs_to_target': runs_to_target
                    }
                    total_balls_bowled_in_over += 1
                    total_balls_bowled += 1
                    ball_outcome_mu = bowling_outcomes_index[
                                          'alpha_for_bowling_outcome_index'].values + beta_by_player_and_bowling_outcome[
                                                                                      batting_team_id,
                                                                                      onstrike_batter_id, :]
                    ball_outcome_p = softmax(ball_outcome_mu)
                    ball_outcome_rv = sps.multinomial(1, ball_outcome_p).rvs(1)
                    ball_outcome = np.where(ball_outcome_rv == 1)[1][0]
                    current_score += bowling_outcomes_index.iloc[ball_outcome]['runs_scored']
                    bowling_outcomes_row = {
                        'match_key': match_key,
                        'innings': innings,
                        'over_number': over,
                        'ball_number_in_over': ball_number_in_over,
                        'bowling_outcome_index': ball_outcome,
                        'bowler_id': selected_bowler_name
                    }
                    match_state_by_ball_and_innings_list.append(match_state_row)
                    bowling_outcome_by_ball_and_innings_list.append(bowling_outcomes_row)
                    if innings == 1 and current_score >= target:
                        break
                    if bowling_outcomes_index.iloc[ball_outcome]['is_legal'] == 1:
                        legal_balls_bowled_in_over += 1
                    if ball_outcome >= 25:
                        # wicket has fallen, find new batsman
                        wickets_lost += 1
                        if wickets_lost == 10:
                            break
                        next_at_bat = wickets_lost + 1
                        batters_dismissed.add(onstrike_batter_id)
                        while onstrike_batter_id in batters_dismissed:
                            onstrike_batter_rv = \
                            sps.multinomial(1, p_batsman_at_position[batting_team_id, next_at_bat, :]).rvs(1)[0]
                            onstrike_batter_id = np.where(onstrike_batter_rv == 1)[0][0]
                            onstrike_batter_name = f"team{batting_team_id}_player{onstrike_batter_id}"
                            onstrike_batter_player_idx = player2idx.loc[onstrike_batter_name]['player_id']
                    if bowling_outcomes_index.iloc[ball_outcome]['batter_switched'] == 1:
                        temp = onstrike_batter_id
                        onstrike_batter_id = offstrike_batter_id
                        offstrike_batter_id = temp
                        temp = onstrike_batter_name
                        onstrike_batter_name = offstrike_batter_name
                        offstrike_batter_name = temp
                        temp = onstrike_batter_player_idx
                        onstrike_batter_player_idx = offstrike_batter_player_idx
                        offstrike_batter_player_idx = temp
                bowler_overs_bowled[selected_bowler_id] += 1
                if wickets_lost == 10 or (innings == 1 and current_score >= target):
                    break
            if innings == 0:
                target = current_score + 1
            match_stats[innings] = {'score': current_score, 'wickets_lost': wickets_lost}
        if match_stats[0]['score'] > match_stats[1]['score']:
            match_stats['winner'] = match_df['innings1_batting_team'].iloc[0]
        elif match_stats[0]['score'] == match_stats[1]['score']:
            match_stats_winner = 'draw'
        else:
            match_stats['winner'] = match_df['innings2_batting_team'].iloc[0]
        match_stats_list.append(match_stats)
    match_state_by_ball_and_innings_df = pd.DataFrame(match_state_by_ball_and_innings_list)
    bowling_outcomes_by_ball_and_innings_df = pd.DataFrame(bowling_outcome_by_ball_and_innings_list)

    yield bowling_outcomes_by_ball_and_innings_df, match_state_by_ball_and_innings_df, player_id, bowling_outcomes_index

@pytest.fixture
def simulate_fake_data():
    full_sample_size = 200
    num_batters = 120
    num_outcomes = 31
    p_batter = sps.dirichlet.rvs(np.ones(num_batters), size=1)[0]
    batter_rv = sps.multinomial(1, p_batter).rvs(full_sample_size)
    alpha_rv = sps.norm(0, 1).rvs(size=num_outcomes)
    beta_rv = np.array([sps.norm(0, 1).rvs(size=num_outcomes)
                        for player in range(num_batters)])
    mu_rv = alpha_rv + np.dot(batter_rv, beta_rv)
    bowling_outcomes_p_rv = softmax(mu_rv, axis=0)
    bowling_outcome_encoded_rv = np.array(
        [sps.multinomial(1, bowling_outcomes_p_rv[i]).rvs(1)[0] for i in range(full_sample_size)])
    bowling_outcome_rv = np.where(bowling_outcome_encoded_rv == 1)[1]
    yield batter_rv, bowling_outcome_encoded_rv, bowling_outcome_rv

def prepare_data_selection_for_batter_runs_model(data_selection_instance,
                                                 selection_type):
    tournaments = data_selection_instance.historical_data_helper.tournaments
    tournaments.set_testing_details("Indian Premier League", "2009")
    seasons_df = tournaments.get_tournament_and_season_details()
    end_date = tournaments.get_first_testing_date()
    start_date = seasons_df[seasons_df['date'] < end_date]['date'].min()
    tournaments.set_training_window(start_date, end_date)
    selection_options = {
        'or_selection': DataSelectionType.OR_SELECTION,
        'and_selection': DataSelectionType.AND_SELECTION
    }
    data_selection_instance.set_selection_type(selection_options[selection_type])

@pytest.fixture
def batter_runs_model(setup_and_teardown):
    test_case, config_instance = setup_and_teardown
    rewards_config = RewardsConfiguration(config_instance)

    helper = Helper(config_instance)

    data_selection = DataSelection(helper)

    simulator = PerfectSimulator(data_selection, rewards_config)
    prepare_data_selection_for_batter_runs_model(simulator.data_selection,
                                                 test_case['selection_type'])

    model_directory_path = config_instance.get_batter_runs_model_info()['model_directory_path']
    model_type = test_case['model_type']
    model = BatterRunsModel(simulator,
                            model_directory_path=model_directory_path,
                            model_type=model_type)

    yield model

