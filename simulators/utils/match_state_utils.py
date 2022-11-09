import pandas as pd
import logging


# This class contains a bunch of functions which are used to calculate the dataframe in
# get_match_state_by_ball_and_innings()

def initialise_match_state(data_selection, is_testing: bool) -> (pd.DataFrame, pd.DataFrame, pd.DataFrame):
    innings_df = data_selection.get_innings_for_selected_matches(is_testing)
    matches_df = data_selection.get_selected_matches(is_testing)
    logging.info("Getting frequent players universe")
    player_universe_df = data_selection.get_frequent_players_universe()

    logging.info("Merging with frequent players")
    index_columns = ['match_key', 'inning', 'over', 'ball']
    other_columns = ['batter', 'bowler', 'batting_team', 'total_runs', 'is_wicket', 'target_runs', 'target_overs']
    match_state_df = innings_df.filter(index_columns + other_columns, axis=1)

    match_state_df = pd.merge(match_state_df, player_universe_df[["featured_player"]],
                              left_on="batter", right_index=True, how='left')

    match_state_df.rename(columns={"featured_player": "batting_featured_player"}, inplace=True)

    match_state_df = pd.merge(match_state_df, player_universe_df[["featured_player"]],
                              left_on="bowler", right_index=True, how='left')

    match_state_df.rename(columns={"featured_player": "bowling_featured_player"}, inplace=True)

    match_state_df = pd.merge(match_state_df, matches_df[["key", "team1", "team2", 'venue']],
                              left_on="match_key", right_on="key", how='left')
    match_state_df.drop('key', axis=1, inplace=True)

    match_state_df = match_state_df.fillna(False)

    return match_state_df, player_universe_df, index_columns


def identify_featured_player(row, is_batter):
    if is_batter:
        header = 'batter'
        key = row["batter"]
        featured_player = row["batting_featured_player"]
    else:
        header = 'bowler'
        key = row["bowler"]
        featured_player = row["bowling_featured_player"]

    if featured_player:
        return f"{header}_{key}"
    else:
        return f"{header}_non_frequent_player"


def identify_featured_player_for_type(match_state_df, label_name, is_batter):
    if is_batter:
        header = 'batter'
        featured_player_label = "batting_featured_player"
    else:
        header = 'bowler'
        featured_player_label = "bowling_featured_player"

    mask = match_state_df[featured_player_label] == True
    match_state_df[label_name] = f"{header}_non_frequent_player"
    match_state_df.loc[mask, label_name] = header + "_" + match_state_df[header]


def setup_data_labels(match_state_df):
    identify_featured_player_for_type(match_state_df, "batting_labels", True)
    identify_featured_player_for_type(match_state_df, "bowling_labels", False)

    match_state_df['bowling_team'] = match_state_df['team1']
    mask = match_state_df['team1'] == match_state_df['batting_team']
    match_state_df.loc[mask, 'bowling_team'] = match_state_df['team2']

    match_state_df['over_number'] = match_state_df['over'] + 1
    mask = match_state_df['over_number'] > 21
    match_state_df.loc[mask, 'over_number'] = 21

    match_state_df['ball_number_in_over'] = match_state_df['ball']
    mask = match_state_df['ball_number_in_over'] > 7
    match_state_df.loc[mask, 'ball_number_in_over'] = 7

    match_state_df.drop('team1', axis=1, inplace=True)
    match_state_df.drop('team2', axis=1, inplace=True)


def get_ball_number(row):
    ball_number = row["ball"]
    if ball_number > 6:
        return 7
    else:
        return ball_number


def get_over_number(row):
    over_number = row["over"]
    if over_number > 20:
        return 21
    else:
        return over_number + 1


def identiy_bowling_team(row):
    team1 = row["team1"]
    team2 = row["team2"]
    batting_team = row["batting_team"]
    if batting_team == team1:
        return team2
    else:
        return team1


def setup_data_labels_with_training(data_selection, match_state_df):
    training_teams = data_selection.get_selected_teams(is_testing=False)

    match_state_df['batting_team_labels'] \
        = match_state_df.apply(
        lambda x: calculate_labels_from_reference_data(x, "batting_team", "batting_team", "not_in_training",
                                                       training_teams), axis=1)
    match_state_df['bowling_team_labels'] = match_state_df.apply(
        lambda x: calculate_labels_from_reference_data(x, "bowling_team", "bowling_team", "not_in_training",
                                                       training_teams), axis=1)

    venues = data_selection.get_selected_venues(is_testing=False)
    match_state_df['venue_labels'] = match_state_df.apply(
        lambda x: calculate_labels_from_reference_data(x, "venue", "venue", "not_in_training", venues), axis=1)

    return training_teams, venues


def calculate_labels_from_reference_data(row, column_name, output_label_suffix, not_found_suffix, reference_list):
    value_found = row[column_name]
    if value_found in reference_list:
        return f"{output_label_suffix}_{value_found}"
    else:
        return f"{output_label_suffix}_{not_found_suffix}"


def add_missing_columns(df, column, default_value):
    if column not in df.columns:
        df[column] = default_value


def calculate_ball_by_ball_stats(match_state_df, index_columns):
    grouped_df = pd.DataFrame()

    # Calculate total stats at a match & innings level
    logging.info(f"Calculating match / inning stats: {match_state_df.shape}")

    logging.info(f"Option 1")

    grouping = match_state_df.groupby(['match_key', 'inning'])
    match_state_df['total_balls_bowled'] = grouping['venue'].cumcount()
    match_state_df['current_total'] = grouping['total_runs'].cumsum()
    match_state_df['wickets_fallen'] = grouping['is_wicket'].cumsum()

    match_state_df['runs_to_target'] = -1
    mask = match_state_df['target_runs'] != -1
    match_state_df.loc[mask, 'runs_to_target'] = match_state_df['target_runs'] - match_state_df['current_total']

    return match_state_df
