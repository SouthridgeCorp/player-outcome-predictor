import pandas as pd
import logging
logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)
logger = logging.getLogger(__name__)


# This class contains a bunch of functions which are used to calculate the dataframe in
# get_match_state_by_ball_and_innings()

def initialise_match_state(data_selection, is_testing: bool) -> (pd.DataFrame, pd.DataFrame, pd.DataFrame):

    logger.debug("Getting selected innings")
    innings_df = data_selection.get_innings_for_selected_matches(is_testing)

    logger.debug("Getting selected matches")
    matches_df = data_selection.get_selected_matches(is_testing)

    logger.debug("Getting player universe")
    player_universe_df = data_selection.get_frequent_players_universe()

    logger.debug("Setting up filters & merges")

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
    logger.debug("Done initialising match state")

    return match_state_df, player_universe_df, index_columns


def identify_featured_player_for_type(match_state_df, label_name, is_batter):
    """
    Creates a new column 'label_name' in match_state_df and updates with the label for the batter or bowler, depending
    on whether they are featured players or not
    """
    if is_batter:
        header = 'batter'
        featured_player_label = "batting_featured_player"
    else:
        header = 'bowler'
        featured_player_label = "bowling_featured_player"

    mask = match_state_df[featured_player_label] == True
    match_state_df[label_name] = f"{header}_non_frequent_player"
    match_state_df.loc[mask, label_name] = header + "_" + match_state_df[header]


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


def setup_data_labels_with_references(match_state_df, column_name, reference_list):
    """
    Creates a new column 'column_name'_labels in match_state_df and populates it with the corresponding label.
    If the 'column_name' value is not in the reference list, indicates that the value is missing in training
    """
    match_state_df[f'{column_name}_labels'] = f"{column_name}_not_in_training"

    mask = match_state_df[column_name].isin(reference_list)
    match_state_df.loc[mask, f'{column_name}_labels'] = column_name + "_" + match_state_df[column_name]


def setup_data_labels_with_references(match_state_df, column_name, reference_list):
    match_state_df[f'{column_name}_labels'] = f"{column_name}_not_in_training"

    mask = match_state_df[column_name].isin(reference_list)
    match_state_df.loc[mask, f'{column_name}_labels'] = column_name + "_" + match_state_df[column_name]

def setup_data_labels_with_training(data_selection, match_state_df):
    logging.info("Getting selections")
    training_teams = data_selection.get_selected_teams(is_testing=False)
    venues = data_selection.get_selected_venues(is_testing=False)

    setup_data_labels_with_references(match_state_df, 'batting_team', training_teams)
    setup_data_labels_with_references(match_state_df, 'bowling_team', training_teams)
    setup_data_labels_with_references(match_state_df, 'venue', venues)
    return training_teams, venues


def add_missing_columns(df, column, default_value):
    if column not in df.columns:
        df[column] = default_value


def calculate_ball_by_ball_stats(match_state_df, index_columns):
    grouped_df = pd.DataFrame()

    # Calculate total stats at a match & innings level
    grouping = match_state_df.groupby(['match_key', 'inning'])
    match_state_df['total_balls_bowled'] = grouping['venue'].cumcount()
    match_state_df['current_total'] = grouping['total_runs'].cumsum()
    match_state_df['wickets_fallen'] = grouping['is_wicket'].cumsum()

    match_state_df['runs_to_target'] = -1
    mask = match_state_df['target_runs'] != -1
    match_state_df.loc[mask, 'runs_to_target'] = match_state_df['target_runs'] - match_state_df['current_total']

    return match_state_df
