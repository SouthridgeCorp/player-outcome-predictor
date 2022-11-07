import pandas as pd

# This class contains a bunch of functions which are used to calculate the dataframe in
# get_match_state_by_ball_and_innings()

def initialise_match_state(data_selection, is_testing: bool) -> (pd.DataFrame, pd.DataFrame, pd.DataFrame):
    innings_df = data_selection.get_innings_for_selected_matches(is_testing)
    matches_df = data_selection.get_selected_matches(is_testing)
    player_universe_df = data_selection.get_frequent_players_universe()

    index_columns = ['match_key', 'inning', 'over', 'ball']
    other_columns = ['batter', 'bowler', 'batting_team', 'total_runs', 'is_wicket']
    match_state_df = innings_df.filter(index_columns + other_columns, axis=1)

    match_state_df = pd.merge(match_state_df, player_universe_df[["featured_player"]],
                              left_on="batter", right_index=True)

    match_state_df.rename(columns={"featured_player": "batting_featured_player"}, inplace=True)

    match_state_df = pd.merge(match_state_df, player_universe_df[["featured_player"]],
                              left_on="bowler", right_index=True)

    match_state_df.rename(columns={"featured_player": "bowling_featured_player"}, inplace=True)

    match_state_df = pd.merge(match_state_df, matches_df[["key", "team1", "team2", 'venue']],
                              left_on="match_key", right_on="key")
    match_state_df.drop('key', axis=1, inplace=True)

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


def setup_data_labels(match_state_df):
    match_state_df['batting_labels'] = match_state_df.apply(lambda x: identify_featured_player(x, True), axis=1)
    match_state_df['bowling_labels'] = match_state_df.apply(lambda x: identify_featured_player(x, False), axis=1)
    match_state_df['bowling_team'] = match_state_df.apply(lambda x: identiy_bowling_team(x), axis=1)
    match_state_df['over_number'] = match_state_df.apply(lambda x: get_over_number(x), axis=1)
    match_state_df['ball_number_in_over'] = match_state_df.apply(lambda x: get_ball_number(x), axis=1)
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
    for g, g_df in match_state_df.groupby(['match_key', 'inning']):
        g_df['total_balls_bowled'] = g_df.reset_index().index
        g_df['wickets_fallen'] = g_df['is_wicket'].cumsum()
        g_df['current_total'] = g_df['total_runs'].cumsum()
        grouped_df = pd.concat([grouped_df, g_df])

    match_state_df = pd.merge(match_state_df, grouped_df['total_balls_bowled'], left_index=True, right_index=True)
    match_state_df = pd.merge(match_state_df, grouped_df['wickets_fallen'], left_index=True, right_index=True)
    match_state_df = pd.merge(match_state_df, grouped_df['current_total'], left_index=True, right_index=True)

    # Calculate runs to target
    grouped_df = pd.DataFrame()
    for g, g_df in match_state_df.groupby(['match_key']):
        g_df = g_df.reset_index()
        total_runs_scored = g_df[g_df['inning'] == 1].iloc[-1]['current_total']
        g_df['runs_to_target'] = g_df.apply(
            lambda x: total_runs_scored - x['current_total'] if x['inning'] == 2 else 0, axis=1)
        grouped_df = pd.concat([grouped_df, g_df])

    grouped_df.set_index(index_columns, inplace=True, verify_integrity=True)
    grouped_df = grouped_df.sort_values(index_columns)

    match_state_df = pd.merge(match_state_df, grouped_df['runs_to_target'], left_index=True, right_index=True)
    return match_state_df
