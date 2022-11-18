import logging

from data_selection.data_selection import DataSelection
from rewards_configuration.rewards_configuration import RewardsConfiguration

import pandas as pd
from simulators.utils.outcomes_calculator import get_base_rewards, get_bonus_penalty, \
    get_all_outcomes_by_ball_and_innnings
from simulators.utils.match_state_utils import setup_data_labels, initialise_match_state, \
    setup_data_labels_with_training, add_missing_columns, calculate_ball_by_ball_stats
from simulators.utils.utils import aggregate_base_rewards
from sklearn.metrics import mean_absolute_error as mae, mean_absolute_percentage_error as mape


class Granularity:
    """
    Structure to represent acceptable levels of granularity
    """
    TOURNAMENT = "tournament"
    STAGE = "tournament_stage"
    MATCH = "match"
    INNING = "innings"


class PerfectSimulator:

    def __init__(self,
                 data_selection: DataSelection,
                 rewards_configuration: RewardsConfiguration):
        self.data_selection = data_selection
        self.rewards_configuration = rewards_configuration

    def get_bowling_outcomes_by_ball_and_innings(self,
                                                 is_testing: bool) -> pd.DataFrame:
        """
        Returns a dataframe with bowling get_outcome_labels by ball and innings mapped as below:
            - [0, 1-b, 1-oe, 1-nb, 1-w,  2-b…. 6-b, 6-oe, 6-nb, 6-w, W-b, W-nb]
            - 0 : dot_ball
            - 1-b : 1 run, attributable to batsman
            - 1-nb: 1 run, attributable to no ball
            - 1-w: 1 run, attributable to wide
            - 1-oe: 1 run, attributable to other extras
            - ... for upto 6 runs
            - W-b: wicket, attributable to bowler along
            - W-bc: wicket, catch, attributable to bowler and fielder
            - W-bs: wicket, stumping, attributable to bowler and fielder
            - W-dro: wicket, direct run-out
            - W-idro: wicket, indirect run-out
            - W-others: other forms of dismissal not attributable to bowler
            Note: No-balls and wickets may also include runs to be attributed to the batter or bowler. These are
            represented through combination labels.
        df schema:
            index: [match_key, innings, over_number, ball_number, bowler]
            columns: bowling_outcomes_index, bowler_id
            values: [one of 0, 1-b, 1-oe, 1-nb, 1-w,  2-b…. 6-b, 6-oe, 6-nb, 6-w, W-b, W-nb and combinations of
            batter & extra runs scored with a no-ball or a wicket]

        :param is_testing: Set True if testing data is needed, else set False
        :return: pd.DataFrame listing bowling get_outcome_labels for each ball in each innings in training/testing matches for
        selected tournaments
        """
        # Calculate all get_outcome_labels with labels
        bowling_outcomes_df = get_all_outcomes_by_ball_and_innnings(self.data_selection, is_testing)

        # Drop the fields we are not interested in
        bowling_outcomes_df.drop('batter_outcome_index', axis=1, inplace=True)
        bowling_outcomes_df.drop('non_striker_outcome_index', axis=1, inplace=True)
        bowling_outcomes_df.drop('fielding_outcome_index', axis=1, inplace=True)

        return bowling_outcomes_df

    def get_match_state_by_ball_and_innings(self,
                                            is_testing: bool) -> pd.DataFrame:
        """
        Returns a dataframe representing the state of the match before a given ball in a given innings was bowled:
        df schema:
            index: [match_key, innings, over_number, ball_number]
            columns:
                [
                - `batter_{id}` (one-hot encoded on the universe of top 11 most frequently featured players in each team
                + 1 column for not_frequent_player i.e if the batsman_id is a player who is not one of the top 11 most
                frequently featured players, then we should get a 1 in in the 'not_frequent_player' column. The effect
                of this is to ensure total number of columns = (number_of_featured_players) + 1
                NOTE: the universe of ids should always be determined on the training set even if we are being queried for
                the testing set.)
                - `bowler_{id}` (one-hot encoded, similar to above, should index into the same list of player ids as for batsmen)
                - `batting_team_id` (one-hot encoded on universe of all teams in training dataset)
                - `bowling_team_id` (one-hot encoded on universe of all teams in training dataset)
                - `over_number` (one-hot encoded, 1 to 21, 21 = super over)
                - `ball_number_in_over` (one-hot encoded, 1 to 7, 7 = any ball bowled beyond regulation 6 balls)
                - `venue_id` (one-hot encoded on universe of all venues in training dataset)
                - `total_balls_bowled` (number of balls bowled in the innings so far)
                - `wickets_fallen` (number of wickets fallen in the innings so far)
                - `current_total` (number of runs conceded in the innings so far)
                - `runs_to_target` (number of runs remaining to win to if second innings]
                ]
            values:depending on the column as described above

        :param is_testing: Set True if testing data is needed, else set False
        :return: pd.DataFrame listing match_state for each ball in each innings in training/testing matches for
        selected tournaments
        """
        match_state_df, player_universe_df, index_columns = initialise_match_state(self.data_selection, is_testing)
        setup_data_labels(match_state_df)
        training_teams, venues = setup_data_labels_with_training(self.data_selection, match_state_df)

        match_state_df = pd.get_dummies(match_state_df, columns=['batting_labels', 'bowling_labels', 'venue_labels',
                                                                 'batting_team_labels', 'bowling_team_labels'],
                                        prefix="", prefix_sep="")
        match_state_df = pd.get_dummies(match_state_df, columns=['over_number', 'ball_number_in_over'])

        columns_to_check = ['over_number_21', 'ball_number_in_over_7', 'batter_non_frequent_player',
                            'bowler_non_frequent_player', 'batting_team_not_in_training',
                            'bowling_team_not_in_training', 'venue_not_in_training']

        for column in columns_to_check:
            add_missing_columns(match_state_df, column, 0)

        for venue in venues:
            add_missing_columns(match_state_df, f"venue_{venue}", 0)

        for team in training_teams:
            add_missing_columns(match_state_df, f"batting_team_{team}", 0)
            add_missing_columns(match_state_df, f"bowling_team_{team}", 0)

        featured_player_list = player_universe_df[player_universe_df['featured_player'] == True].index.tolist()
        match_state_columns = match_state_df.columns.values.tolist()
        for featured_player in featured_player_list:
            expected_columns = [f"batter_{featured_player}", f"bowler_{featured_player}"]
            for expected_column in expected_columns:
                if expected_column not in match_state_columns:
                    match_state_df[expected_column] = 0

        match_state_df.set_index(index_columns, inplace=True, verify_integrity=True)
        match_state_df = match_state_df.sort_values(index_columns)

        match_state_df = calculate_ball_by_ball_stats(match_state_df, index_columns)
        return match_state_df

    def get_batting_outcomes_by_ball_and_innings(self, is_testing: bool) -> pd.DataFrame:
        """
        Returns a dataframe representing mutually exclusive get_outcome_labels for a batter, composed of
        - [0, 1-b, 2-b, 3-b, 4-b, 5-b, 6-b, W, E]
        - 0 : dot_ball, and other bowling_outcomes not attributable to batsman, excluding wickets
        - 1-b: same as 1-b get_bowling_outcome_label
        - ... for upto 6 runs
        - W: union of W-b, W-bc, W-bs, W-dro, W-idro, W-others from get_bowling_outcome_label
         Note: Wickets may also include runs to be attributed to the batter. These are represented through
         combination labels.
        df schema:
            index: [match_key, innings, over_number, ball_number]
            columns: batting_outcomes_index, batter_id
            values: [one of 0, 1-b, 2-b, 3-b, 4-b, 5-b, 6-b, W, E, combination of runs & wickets]

        :param is_testing: Set True if testing data is needed, else set False
        :return: pd.DataFrame listing batting get_outcome_labels for each ball in each innings in training/testing matches for
        selected tournaments
        """

        # Get all get_outcome_labels
        df = get_all_outcomes_by_ball_and_innnings(self.data_selection, is_testing)

        # Drop the fields we are not interested in
        df.drop('bowler', axis=1, inplace=True)
        df.drop('bowling_outcome_index', axis=1, inplace=True)

        df.drop('fielder', axis=1, inplace=True)
        df.drop('fielding_outcome_index', axis=1, inplace=True)

        return df

    def get_fielding_outcomes_by_ball_and_innings(self, is_testing: bool) -> pd.DataFrame:
        """
        Returns a dataframe representing mutually exclusive get_outcome_labels for a fielder, composed of
            - [w-c,w-s,w-dro,w-idro,nfo]
            - w-c: catch,
            - w-s: stumping
            - w-dro: direct run out
            - w-idro: indirect run out
            - nfo: no fielding outcome
        df schema:
            index: [match_key, innings, over_number, ball_number]
            columns: fielding_outcomes_index, fielder_id (created from same universe of frequently featured players,
            set to nan if outcome = nfo)
            values: [one of w-c,w-s,w-dro,w-idro,nfo]
        :param is_testing: Set True if testing data is needed, else set False
        :return: pd.DataFrame listing fielding get_outcome_labels for each ball in each innings in training/testing matches for
        selected tournaments
        """
        # Get all get_outcome_labels
        df = get_all_outcomes_by_ball_and_innnings(self.data_selection, is_testing)

        # Drop the fields we are not interested in
        df.drop('bowler', axis=1, inplace=True)
        df.drop('bowling_outcome_index', axis=1, inplace=True)

        df.drop('batter', axis=1, inplace=True)
        df.drop('batter_outcome_index', axis=1, inplace=True)

        df.drop('non_striker', axis=1, inplace=True)
        df.drop('non_striker_outcome_index', axis=1, inplace=True)

        return df

    def get_outcomes_by_ball_and_innings(self, is_testing: bool, generate_labels=True) -> pd.DataFrame:
        """Returns a dataframe representing all get_outcome_labels at a ball and innings level for the train/test dataset
        df schema:
            index: [match_key, innings, over_number, ball_number]
            columns: [
                    bowling_outcomes_index,
                    bowler_id,
                    batting_outcomes_index,
                    batter_id,
                    fielding_outcomes_index,
                    fielder_id
                    ]
        See `outcomes_by_ball_and_innings` subgraph of the computational model
        :param is_testing: Set True if testing data is needed, else set False
        :param generate_labels: Indicates whether labels should be calculated or not. If not calculated, this function
        returns all the different fields that represent all batting, fielding & bowling get_outcome_labels
        :return: pd.DataFrame as above"""
        df = get_all_outcomes_by_ball_and_innnings(self.data_selection, is_testing, generate_labels)
        return df

    def get_outcomes_by_player_and_innings(self,
                                           is_testing: bool) -> pd.DataFrame:
        """Returns a dataframe representing all get_outcome_labels at a player and innings level for the train/test dataset
        df schema:
            index: [match_key, innings, team_id, player_id]
            columns: [
                    bowling_economy_rate,
                    batting_strike_rate,
                    wickets_taken
                    ]
        See `outcomes_by_player_and_innings` subgraph of the computational model
        :param is_testing: Set True if testing data is needed, else set False
        :return: pd.DataFrame as above"""

        innings_df = self.data_selection.get_innings_for_selected_matches(is_testing)
        matches_df = self.data_selection.get_selected_matches(is_testing)

        innings_df = pd.merge(innings_df, matches_df[['key', 'tournament_key', 'stage']],
                              left_on='match_key', right_on='key')

        outcomes_list = []
        # Calculate the batting strike rate
        for g, g_df in innings_df.groupby(['match_key', 'inning', 'batting_team', 'batter']):
            total_balls_bowled = len(g_df)
            total_runs_made = g_df['batter_runs'].sum()
            batting_strike_rate = 100 * total_runs_made / total_balls_bowled
            outcomes_list.append({'match_key': g[0], 'inning': g[1], 'team': g[2],
                                  'player_key': g[3], 'strike_rate': batting_strike_rate,
                                  'total_balls': total_balls_bowled, 'batting_total_runs': total_runs_made})

        # Calculate the bowling econ rate & number of wickets
        for g, g_df in innings_df.groupby(['match_key', 'inning', 'bowling_team', 'bowler']):
            number_of_overs = len(g_df['over'].unique())
            total_runs_made = g_df['total_runs'].sum()
            number_of_wickets = g_df['is_wicket'].sum()

            # Runouts are not credited to the bowler
            number_of_runouts = len(g_df[g_df['dismissal_kind'] == 'run out'])
            number_of_wickets -= number_of_runouts
            economy_rate = total_runs_made / number_of_overs

            outcomes_list.append({'match_key': g[0], 'inning': g[1], 'team': g[2],
                                  'player_key': g[3], 'economy_rate': economy_rate, 'wickets_taken': number_of_wickets,
                                  'number_of_overs': number_of_overs, 'total_runs': total_runs_made})

        outcomes_df = pd.DataFrame(data=outcomes_list)
        index_columns = ['match_key', 'inning', 'team', 'player_key']

        outcomes_df = pd.merge(outcomes_df, matches_df[['key', 'tournament_key', 'stage']],
                               left_on='match_key', right_on='key')
        outcomes_df.drop('key', axis=1, inplace=True)

        outcomes_df.set_index(index_columns, inplace=True, verify_integrity=True)
        outcomes_df = outcomes_df.sort_values(index_columns)

        return outcomes_df

    def get_outcomes_by_team_and_innings(self,
                                         is_testing: bool, input_player_outcomes=None) -> pd.DataFrame:
        """Returns a dataframe representing all get_outcome_labels at a player and innings level for the train/test dataset
        df schema:
            index: [match_key, innings, team_id]
            columns: [
                    bowling_economy_rate,
                    batting_strike_rate
                    ]
        See `outcomes_by_team_and_innings` subgraph of the computational model
        :param is_testing: Set True if testing data is needed, else set False
        :param input_player_outcomes: If specified, used as the basis for all the calculation in this function, else
        a call to get_outcomes_by_player_and_innings() gets the required data. Use this as a perf optimisation.
        :return: pd.DataFrame as above"""

        if input_player_outcomes is not None:
            player_outcomes = input_player_outcomes.copy()
        else:
            player_outcomes = self.get_outcomes_by_player_and_innings(is_testing)
        innings_outcomes_list = []

        # Calculate all the fields for player get_outcome_labels
        for g, g_df in player_outcomes.groupby(['match_key', 'inning', 'team']):
            total_runs = g_df['total_runs'].sum()
            total_balls = g_df['total_balls'].sum()
            batting_total_runs = g_df['batting_total_runs'].sum()
            number_of_overs = g_df['number_of_overs'].sum()
            economy_rate = (total_runs / number_of_overs) if number_of_overs != 0 else 0
            strike_rate = (100 * batting_total_runs / total_balls) if total_balls != 0 else 0
            innings_outcomes_list.append({'match_key': g[0], 'inning': g[1], 'team': g[2],
                                          'inning_economy_rate': economy_rate, 'inning_strike_rate': strike_rate,
                                          'inning_number_of_overs': number_of_overs, 'inning_total_runs': total_runs,
                                          'inning_total_balls': total_balls,
                                          'inning_batting_total_runs': batting_total_runs})

        innings_outcomes_df = pd.DataFrame(data=innings_outcomes_list)
        index_columns = ['match_key', 'inning', 'team']
        innings_outcomes_df.set_index(index_columns, inplace=True, verify_integrity=True)
        innings_outcomes_df = innings_outcomes_df.sort_values(index_columns)
        return innings_outcomes_df

    def get_rewards_components(self,
                               is_testing: bool, generate_labels=False) -> (pd.DataFrame, pd.DataFrame):
        """Returns 2 dataframes:
        base_rewards_by_ball_and_innings: represents base rewards of all types calculated at a ball and innings level
        for the train/test dataset
        df schema:
            index: [match_key, innings, over_number, ball_number]
            columns: [
                    bowling_base_rewards,
                    bowler_id,
                    batting_base_rewards,
                    batter_id,
                    fielding_base_rewards,
                    fielder_id
                    ]
        bonus_penalty_by_ball_and_innings: represents bonus/penalty of all types calculated at the innings level
        for the train/test dataset
        df schema:
            index: [match_key, innings, team_id, player_id]
            columns: [
                    bowling_bonus_wickets,
                    bowling_bonus,
                    bowling_penalty,
                    batting_bonus,
                    batting_penalty
                    ]
        See `rewards` subgraph of the computational model
        :param is_testing: Set True if testing data is needed, else set False
        :param generate_labels: Set to true if get_outcome_labels labels should be generated, else False
        :return: pd.DataFrame as above"""

        logging.debug("Getting ball & inning outcomes")
        outcomes_df = self.get_outcomes_by_ball_and_innings(is_testing, generate_labels)

        logging.debug("Calculating base rewards")
        outcomes_df['batter_base_rewards'], outcomes_df['non_striker_base_rewards'], \
        outcomes_df['bowling_base_rewards'], outcomes_df['fielding_base_rewards'] = zip(*outcomes_df.apply(
            lambda x: get_base_rewards(x, self.rewards_configuration), axis=1))

        logging.debug("Getting player outcomes by innings")

        bonus_penalty_df = self.get_outcomes_by_player_and_innings(is_testing)

        logging.debug("Calculating outcomes by team and innings")
        team_stats_df = self.get_outcomes_by_team_and_innings(is_testing, bonus_penalty_df)

        logging.debug("Aggregating base rewards")

        # Calculate cumulative base rewards per player
        base_rewards_per_player_dict = {}
        aggregate_base_rewards(outcomes_df, 'batting_team', 'batter', 'batter_base_rewards', 'batter_base_rewards',
                               base_rewards_per_player_dict)
        aggregate_base_rewards(outcomes_df, 'batting_team', 'non_striker', 'non_striker_base_rewards',
                               'batter_base_rewards', base_rewards_per_player_dict)
        aggregate_base_rewards(outcomes_df, 'bowling_team', 'fielder', 'fielding_base_rewards',
                               'fielding_base_rewards', base_rewards_per_player_dict)
        aggregate_base_rewards(outcomes_df, 'bowling_team', 'bowler', 'bowling_base_rewards',
                               'bowling_base_rewards', base_rewards_per_player_dict)

        base_rewards_per_player_list = []

        for key in base_rewards_per_player_dict.keys():
            base_rewards_per_player_list.append(base_rewards_per_player_dict[key])

        base_rewards_per_player_df = pd.DataFrame(data=base_rewards_per_player_list)
        index_columns = ['match_key', 'inning', 'team', 'player_key']
        base_rewards_per_player_df.set_index(index_columns, inplace=True, verify_integrity=True)
        base_rewards_per_player_df = base_rewards_per_player_df.sort_values(index_columns)

        logging.debug("Calculating bonus / penalty")

        bonus_penalty_df = pd.merge(bonus_penalty_df,
                                    base_rewards_per_player_df[['batter_base_rewards',
                                                                'fielding_base_rewards', 'bowling_base_rewards']],
                                    left_index=True, right_index=True)

        bonus_penalty_df = pd.merge(bonus_penalty_df,
                                    team_stats_df[['inning_number_of_overs', 'inning_total_runs',
                                                   'inning_total_balls', 'inning_batting_total_runs']],
                                    left_on=['match_key', 'inning', 'team'], right_index=True)

        bonus_penalty_df['bowling_bonus_wickets'], bonus_penalty_df['bowling_bonus'], \
        bonus_penalty_df['bowling_penalty'], bonus_penalty_df['batting_bonus'], \
        bonus_penalty_df['batting_penalty'], bonus_penalty_df['bowling_rewards'], \
        bonus_penalty_df['batting_rewards'], bonus_penalty_df['fielding_rewards'] = zip(*bonus_penalty_df.apply(
            lambda x: get_bonus_penalty(x, self.rewards_configuration), axis=1))

        logging.debug("DONE with rewards")

        return outcomes_df, bonus_penalty_df

    def get_simulation_evaluation_metrics_by_granularity(self,
                                                         is_testing: bool,
                                                         granularity: str) -> pd.DataFrame:
        """Returns a dataframe representing all rewards for a player at the chosen granularity level:
        df schema:
            index: [player_key,
                    granluarity_key - depends on the granularity param,
                    if innings (tournament_key, tournament_stage, match_key, innings), else
                        match: (tournament_key, tournament_stage, match_key)
                        tournament_stage: (tournament_key, tournament_stage)
                        tournament: (tournament_key)
                    ]
            columns: [
                    bowling_rewards,
                    batting_rewards
                    fielding_rewards
                    total_rewards
                    ]
        See `simulation_evaluation_metrics` subgraph of the computational model
        :param is_testing: Set True if testing data is needed, else set False
        :param granularity: The granularity level, must be one of the levels specified in Granularity
        :return: pd.DataFrame as above"""

        logging.debug("Getting rewards components")
        base_rewards_df, bonus_penalty_df = self.get_rewards_components(is_testing)

        group_by_columns = get_index_columns(granularity)
        rewards_df = pd.DataFrame()

        logging.debug(f"Calculating total rewards for {bonus_penalty_df.shape}")

        for g, g_df in bonus_penalty_df.groupby(group_by_columns):
            input_dict = {'number_of_matches': len(g_df.reset_index()['match_key'].unique()),
                          'bowling_rewards': g_df['bowling_rewards'].sum(),
                          'batting_rewards': g_df['batting_rewards'].sum(),
                          'fielding_rewards': g_df['fielding_rewards'].sum()}

            input_dict['total_rewards'] = input_dict['bowling_rewards'] + input_dict['batting_rewards'] \
                                          + input_dict['fielding_rewards']
            i = 0
            for column in group_by_columns:
                input_dict[column] = g[i]
                i += 1
            rewards_df = rewards_df.append(input_dict, ignore_index=True)

        rewards_df = self.data_selection.merge_with_players(rewards_df, 'player_key')

        rewards_df.set_index(group_by_columns, inplace=True, verify_integrity=True)
        logging.debug("Returning the total DF")

        return rewards_df

    def get_error_measures(self,
                           is_testing: bool,
                           contender_simulation_evaluation_metrics: pd.DataFrame,
                           granularity,
                           perfect_simulator_rewards_ref=None) -> pd.DataFrame:
        """Returns a dataframe representing error measures between this simulator's simulation_evaluation_metrics
        and a contender simulators simulation evaluation metrics.
        df schema:
            index: [player_key,
                    granluarity_key - same as contender_simulation_evaluation_metrics
                    ]
            columns: [
                    mean_absolute_error,
                    mean_absolute_percentage_error
                    ]
        :param is_testing: Set True if testing data is needed, else set False
        :param contender_simulation_evaluation_metrics: A df generated by calling another simulator instance's
        get_simulation_evaluation_metrics method at a given granularity. If this is provided as the current simulator's
        simulation_evaluation_metrics, it should result in zero MAE and MAPE at all granularities.
        :param granularity: The granularity level, must be one of the levels specified in Granularity
        :param perfect_simulator_rewards_ref: A reference to the rewards used as the basis for this calculation. If not
        specified, they are calculated via a call to get_simulation_evaluation_metrics_by_granularity(). Use this as a
        perf optimisation.
        :return: pd.DataFrame as above
        :raises: Exception if the contender_simulation_evaluation_metrics does not have a matching index
        to the result of self.get_simulation_evaluation_metrics(is_testing,granularity [as implied by the contender df]"""

        logging.debug("Starting error measure calc")
        if perfect_simulator_rewards_ref is not None:
            perfect_simulator_rewards_df = perfect_simulator_rewards_ref.copy()
        else:
            perfect_simulator_rewards_df = self.get_simulation_evaluation_metrics_by_granularity(is_testing,
                                                                                                 granularity)
        logging.debug("Received baseline data and comparing errors")

        # Make sure the two dataframes are always the same shape. This merge ensures the same number of
        # players are evaluated
        columns_to_compare = ['batting_rewards', 'bowling_rewards', 'fielding_rewards', 'total_rewards']
        perfect_simulator_rewards_df = pd.merge(perfect_simulator_rewards_df,
                                                contender_simulation_evaluation_metrics[columns_to_compare],
                                                left_index=True, right_index=True, suffixes=["_expected", "_received"])
        columns_to_compare = ['batting_rewards', 'bowling_rewards', 'fielding_rewards', 'total_rewards']

        for column in columns_to_compare:
            # calculate the error metrics between expected & received
            perfect_simulator_rewards_df[f'{column}_absolute_error'] = \
                abs(perfect_simulator_rewards_df[f"{column}_expected"] -
                    perfect_simulator_rewards_df[f"{column}_received"])

            perfect_simulator_rewards_df[f'{column}_absolute_percentage_error'] = 0.0
            mask = perfect_simulator_rewards_df[f"{column}_expected"] != 0
            perfect_simulator_rewards_df.loc[mask, f'{column}_absolute_percentage_error'] = \
                abs(100 * perfect_simulator_rewards_df[f'{column}_absolute_error'] / \
                perfect_simulator_rewards_df[f"{column}_expected"])

        logging.debug("Done with error measurements")

        return perfect_simulator_rewards_df


def get_index_columns(granularity):
    """
    Helper function which maps different granularity levels to the corresponding index columns
    """
    group_by_columns = ['player_key', 'tournament_key']

    if granularity == Granularity.INNING:
        group_by_columns = group_by_columns + ['stage', 'match_key', 'inning']
    elif granularity == Granularity.MATCH:
        group_by_columns = group_by_columns + ['stage', 'match_key']
    elif granularity == Granularity.STAGE:
        group_by_columns = group_by_columns + ['stage']

    return group_by_columns
