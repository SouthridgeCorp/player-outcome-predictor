import logging

from data_selection.data_selection import DataSelection
from rewards_configuration.rewards_configuration import RewardsConfiguration

import pandas as pd
from simulators.utils.outcomes_calculator import get_base_rewards, get_bonus_penalty, \
    get_all_outcomes_by_ball_and_innnings
from simulators.utils.match_state_utils import setup_data_labels, initialise_match_state, \
    setup_data_labels_with_training, add_missing_columns, calculate_ball_by_ball_stats
from simulators.utils.utils import aggregate_base_rewards, aggregate_base_rewards_df
from data_selection.data_selection import DataSelectionType

logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)
logger = logging.getLogger(__name__)


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
                                            is_testing: bool,
                                            one_hot_encoding=True) -> pd.DataFrame:
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
        logger.debug("Setting up match state")

        match_state_df, player_universe_df, index_columns = initialise_match_state(self.data_selection, is_testing)

        logger.debug("Setting up data labels")
        setup_data_labels(match_state_df)

        logger.debug("Setting up data labels with training information")
        training_teams, venues = setup_data_labels_with_training(self.data_selection, match_state_df)

        if one_hot_encoding:
            logger.debug("Blowing up the match state df")
            match_state_df = pd.get_dummies(match_state_df, columns=['batting_labels', 'bowling_labels', 'venue_labels',
                                                                     'batting_team_labels', 'bowling_team_labels'],
                                            prefix="", prefix_sep="")
            match_state_df = pd.get_dummies(match_state_df, columns=['over_number', 'ball_number_in_over'])

            columns_to_check = ['over_number_21', 'ball_number_in_over_7', 'batter_non_frequent_player',
                                'bowler_non_frequent_player', 'batting_team_not_in_training',
                                'bowling_team_not_in_training', 'venue_not_in_training']

            logger.debug("Adding missing columns")

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

        logger.debug("Calculating ball by ball stats")
        match_state_df = calculate_ball_by_ball_stats(match_state_df, index_columns)
        logger.debug("Done with match state")

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
                                           is_testing: bool, columns_to_persist=[]) -> pd.DataFrame:
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
        :param columns_to_persist: The list of columns to persist in the output dataframes
        :return: pd.DataFrame as above"""

        innings_df = self.data_selection.get_innings_for_selected_matches(is_testing).copy()
        matches_df = self.data_selection.get_selected_matches(is_testing)

        innings_df = pd.merge(innings_df, matches_df[['key', 'tournament_key', 'stage']],
                              left_on='match_key', right_on='key')

        # Setup counter for runouts
        mask = innings_df['dismissal_kind'] == 'run out'
        innings_df['is_runout'] = 0
        innings_df.loc[mask, 'is_runout'] = 1
        index_columns = ['match_key', 'inning', 'team', 'player_key']

        # Calculate batting outcomes
        batting_df = pd.DataFrame()
        batting_grouping = innings_df.groupby(['match_key', 'inning', 'batting_team', 'batter'])

        # Total balls at the batter level must not include any wides or no-balls bowled
        batting_df['total_balls'] = \
            batting_grouping['batter'].count() - batting_grouping['wides'].count()

        batting_df['batting_total_balls'] = \
            batting_grouping['batter'].count() - batting_grouping['wides'].count() - batting_grouping['noballs'].count()

        # Batter runs should not include extras...
        batting_df['batting_total_runs'] = batting_grouping['batter_runs'].sum()

        # but we still need to account for them when calculating the batting innings total
        batting_df['batting_total_runs_with_extras'] = batting_grouping['total_runs'].sum()

        batting_df['strike_rate'] = 100 * batting_df['batting_total_runs'] / batting_df['total_balls']
        batting_df = batting_df.reset_index()
        batting_df.rename(columns={'batter': 'player_key', 'batting_team': 'team'}, inplace=True)

        # Calculate non striker outcomes - without doing this step, we may end up dropping instances of non-strikers
        # who have never batted at all
        non_striker_df = pd.DataFrame()
        non_striker_grouping = innings_df.groupby(['match_key', 'inning', 'batting_team', 'non_striker'])
        non_striker_df['non_striker_count'] = non_striker_grouping['non_striker'].count()
        non_striker_df = non_striker_df.reset_index()
        non_striker_df.rename(columns={'non_striker': 'player_key', 'batting_team': 'team'}, inplace=True)

        # Calculate bowling outcomes
        bowling_df = pd.DataFrame()
        bowling_grouping = innings_df.groupby(['match_key', 'inning', 'bowling_team', 'bowler'])

        # Bowled deliveries only includes legal deliveries (as per sportiqo)
        bowling_df['number_of_bowled_deliveries'] = \
            bowling_grouping['bowler'].count() - bowling_grouping['wides'].count() - bowling_grouping['noballs'].count()

        byes_sum = 0
        # total runs for the bowler must not include byes & legbyes. Please note that the tournament_simulator may not
        # simulate byes & legbyes, hence we need to add an extra check.
        # TODO: Make the tournament simulator simulate byes & legbyes and get rid of the ugly code below.
        if 'byes' in innings_df.columns:
            byes_sum += bowling_grouping['byes'].sum()
        if 'legbyes' in innings_df.columns:
            byes_sum += bowling_grouping['legbyes'].sum()
        bowling_df['total_runs'] = bowling_grouping['total_runs'].sum() - byes_sum

        # Keep track of the overall bowling total (with extras) since that is used to calc. innings ER
        bowling_df['bowling_total_runs_with_extras'] = bowling_grouping['total_runs'].sum()
        bowling_df['wickets_taken'] = bowling_grouping['is_wicket'].sum() - bowling_grouping['is_runout'].sum()
        bowling_df['economy_rate'] = bowling_df['total_runs'] / bowling_df['number_of_bowled_deliveries']
        bowling_df = bowling_df.reset_index()
        bowling_df.rename(columns={'bowler': 'player_key', 'bowling_team': 'team'}, inplace=True)

        # Calculate fielder outcomes - without doing this step, we may end up dropping instances of fielders who
        # have not bowled or batted at all
        fielding_df = pd.DataFrame()
        fielding_grouping = innings_df.groupby(['match_key', 'inning', 'bowling_team', 'fielder'])
        fielding_df['number_of_fielding_events'] = fielding_grouping['fielder'].count()
        fielding_df = fielding_df.reset_index()
        fielding_df.rename(columns={'fielder': 'player_key', 'bowling_team': 'team'}, inplace=True)

        # Merge all the outcomes together
        outcomes_df = pd.merge(batting_df, bowling_df, left_on=index_columns, right_on=index_columns, how='outer')
        outcomes_df = pd.merge(outcomes_df, fielding_df, left_on=index_columns, right_on=index_columns, how='outer')
        outcomes_df = pd.merge(outcomes_df, non_striker_df, left_on=index_columns, right_on=index_columns, how='outer')

        outcomes_df = pd.merge(outcomes_df, matches_df[['key', 'tournament_key', 'stage'] + columns_to_persist],
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

        index_columns = ['match_key', 'inning', 'team']

        # Calculate innings level outcomes
        new_innings_outcomes_df = pd.DataFrame()
        innings_grouping = player_outcomes.groupby(index_columns)
        new_innings_outcomes_df['inning_batting_total_runs'] = innings_grouping['batting_total_runs_with_extras'].sum()
        new_innings_outcomes_df['inning_total_balls'] = innings_grouping['batting_total_balls'].sum()
        new_innings_outcomes_df['inning_total_runs'] = innings_grouping['bowling_total_runs_with_extras'].sum()
        new_innings_outcomes_df['inning_number_of_bowled_deliveries'] = \
            innings_grouping['number_of_bowled_deliveries'].sum()

        new_innings_outcomes_df['inning_strike_rate'] = 0.0
        mask = new_innings_outcomes_df['inning_total_balls'] != 0
        new_innings_outcomes_df.loc[mask, 'inning_strike_rate'] = \
            (100 * new_innings_outcomes_df['inning_batting_total_runs']) / new_innings_outcomes_df['inning_total_balls']

        new_innings_outcomes_df['inning_economy_rate'] = 0.0
        mask = new_innings_outcomes_df['inning_number_of_bowled_deliveries'] != 0
        new_innings_outcomes_df.loc[mask, 'inning_economy_rate'] = \
            new_innings_outcomes_df['inning_total_runs'] / new_innings_outcomes_df['inning_number_of_bowled_deliveries']

        new_innings_outcomes_df = new_innings_outcomes_df.sort_values(index_columns)

        return new_innings_outcomes_df

    def get_rewards_components(self,
                               is_testing: bool, generate_labels=False, columns_to_persist=[]) -> (
            pd.DataFrame, pd.DataFrame):
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
        :param columns_to_persist: The list of columns to persist in the output dataframes
        :return: pd.DataFrame as above"""

        logger.debug("Getting ball & inning outcomes")
        outcomes_df = self.get_outcomes_by_ball_and_innings(is_testing, generate_labels)

        logger.debug("Calculating base rewards")
        outcomes_df['batter_base_rewards'], outcomes_df['non_striker_base_rewards'], \
        outcomes_df['bowling_base_rewards'], outcomes_df['fielding_base_rewards'] = zip(*outcomes_df.apply(
            lambda x: get_base_rewards(x, self.rewards_configuration), axis=1))

        logger.debug("Getting player outcomes by innings")

        bonus_penalty_df = self.get_outcomes_by_player_and_innings(is_testing, columns_to_persist=columns_to_persist)

        logger.debug("Calculating outcomes by team and innings")
        team_stats_df = self.get_outcomes_by_team_and_innings(is_testing, bonus_penalty_df)

        logger.debug("Aggregating base rewards")

        # Calculate cumulative base rewards per player
        batting_aggregate_df = aggregate_base_rewards_df(outcomes_df, 'batting_team', 'batter',
                                                         'batter_base_rewards', 'batter_base_rewards')
        non_striker_aggregate_df = aggregate_base_rewards_df(outcomes_df, 'batting_team', 'non_striker',
                                                             'non_striker_base_rewards', 'batter_base_rewards')
        fielder_aggregate_df = aggregate_base_rewards_df(outcomes_df, 'bowling_team', 'fielder',
                                                         'fielding_base_rewards', 'fielding_base_rewards')
        bowler_aggregate_df = aggregate_base_rewards_df(outcomes_df, 'bowling_team', 'bowler', 'bowling_base_rewards',
                                                        'bowling_base_rewards')

        # Calculate cumulative batting rewards (also pulling in non-striker rewards
        aggregated_df = pd.merge(batting_aggregate_df, non_striker_aggregate_df, left_index=True, right_index=True,
                                 how="outer")
        aggregated_df = aggregated_df.fillna(0.0)

        aggregated_df['batter_base_rewards'] = \
            aggregated_df['batter_base_rewards_x'] + aggregated_df['batter_base_rewards_y']

        aggregated_df.drop('batter_base_rewards_x', axis=1, inplace=True)
        aggregated_df.drop('batter_base_rewards_y', axis=1, inplace=True)

        aggregated_df = pd.merge(pd.merge(aggregated_df, fielder_aggregate_df, left_index=True, right_index=True,
                                          how="outer"), bowler_aggregate_df, left_index=True, right_index=True,
                                 how="outer")
        aggregated_df = pd.merge(aggregated_df, bonus_penalty_df[['tournament_key', 'stage']],
                                 left_index=True, right_index=True)

        base_rewards_per_player_df = aggregated_df.sort_index()
        logger.debug("Calculating bonus / penalty")


        bonus_penalty_df = pd.merge(bonus_penalty_df,
                                    base_rewards_per_player_df[['batter_base_rewards',
                                                                'fielding_base_rewards', 'bowling_base_rewards']],
                                    left_index=True, right_index=True)

        bonus_penalty_df = pd.merge(bonus_penalty_df,
                                    team_stats_df[['inning_number_of_bowled_deliveries', 'inning_total_runs',
                                                   'inning_total_balls', 'inning_batting_total_runs']],
                                    left_on=['match_key', 'inning', 'team'], right_index=True)

        bonus_penalty_df['bowling_bonus_wickets'], bonus_penalty_df['bowling_bonus'], \
        bonus_penalty_df['bowling_penalty'], bonus_penalty_df['batting_bonus'], \
        bonus_penalty_df['batting_penalty'], bonus_penalty_df['bowling_rewards'], \
        bonus_penalty_df['batting_rewards'], bonus_penalty_df['fielding_rewards'] = zip(*bonus_penalty_df.apply(
            lambda x: get_bonus_penalty(x, self.rewards_configuration), axis=1))

        logger.debug("DONE with rewards")

        return outcomes_df, bonus_penalty_df

    def get_simulation_evaluation_metrics_by_granularity(self,
                                                         is_testing: bool,
                                                         granularity: str,
                                                         columns_to_persist=[]) -> pd.DataFrame:
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

        logger.debug("Getting rewards components")
        base_rewards_df, bonus_penalty_df = self.get_rewards_components(is_testing,
                                                                        columns_to_persist=columns_to_persist)

        group_by_columns = get_index_columns(granularity) + columns_to_persist

        new_rewards_df = pd.DataFrame()
        rewards_grouping = bonus_penalty_df.reset_index().groupby(group_by_columns)
        new_rewards_df['number_of_matches'] = rewards_grouping['match_key'].nunique()
        new_rewards_df['bowling_rewards'] = rewards_grouping['bowling_rewards'].sum()
        new_rewards_df['batting_rewards'] = rewards_grouping['batting_rewards'].sum()
        new_rewards_df['fielding_rewards'] = rewards_grouping['fielding_rewards'].sum()
        new_rewards_df['total_rewards'] = new_rewards_df['batting_rewards'] + new_rewards_df['bowling_rewards'] \
                                        + new_rewards_df['fielding_rewards']

        logger.debug(f"Calculating total rewards for {bonus_penalty_df.shape}")
        new_rewards_df = new_rewards_df.reset_index()
        new_rewards_df = self.data_selection.merge_with_players(new_rewards_df, 'player_key')
        new_rewards_df.set_index(group_by_columns, inplace=True, verify_integrity=True)

        logger.debug("Returning the total DF")

        return new_rewards_df

    def get_error_measures(self,
                           is_testing: bool,
                           contender_simulation_evaluation_metrics: pd.DataFrame,
                           granularity,
                           perfect_simulator_rewards_ref=None,
                           columns_to_persist=[]) -> pd.DataFrame:
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
        :param columns_to_persist: The list of columns to persist in the output dataframes
        :return: pd.DataFrame as above
        :raises: Exception if the contender_simulation_evaluation_metrics does not have a matching index
        to the result of self.get_simulation_evaluation_metrics(is_testing,granularity [as implied by the contender df]"""

        logger.debug("Starting error measure calc")
        if perfect_simulator_rewards_ref is not None:
            perfect_simulator_rewards_df = perfect_simulator_rewards_ref.copy()
        else:
            perfect_simulator_rewards_df = self.get_simulation_evaluation_metrics_by_granularity(
                is_testing, granularity, columns_to_persist=columns_to_persist)
        logger.debug("Received baseline data and comparing errors")

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

        logger.debug("Done with error measurements")

        return perfect_simulator_rewards_df

    def get_match_state_by_balls_for_training(self, calculate_bowling_options=True, one_hot_encoding=True) \
            -> (pd.DataFrame, pd.DataFrame, dict):
        """
        Gets the match state for the specified selection type. If requested, also gets the corresponding bowling options
        :param calculate_bowling_options: If true, the bowling options for the corresponding selection type is returned.
        If false, an empty dataframe is returned for bowling options.
        :param one_hot_encoding: If true, the match state columns for batter, bowler, venue, over, ball and innings are
        one-hot encoded
        :return: dataframe for match state, dataframe for bowling outcomes and a set of stats representing the deviation
        from the raw data
        """
        logger.info("Getting match state by balls and innings")
        unqualified_train_match_state_df = self.get_match_state_by_ball_and_innings(False, one_hot_encoding)

        logger.debug("Getting selected matches")
        test_season_matches = self.data_selection.get_selected_matches(True)

        logger.debug("Getting selected innings")
        test_season_innings = self.data_selection.get_innings_for_selected_matches(True)

        logger.debug("Applying masks")

        test_season_venues = test_season_matches.venue.unique().tolist()
        test_season_batters = test_season_innings.batter.unique().tolist()
        test_season_bowlers = test_season_innings.bowler.unique().tolist()

        is_test_season_venue = unqualified_train_match_state_df.venue.isin(test_season_venues)
        is_test_season_batter = unqualified_train_match_state_df.batter.isin(test_season_batters)
        is_test_season_bowler = unqualified_train_match_state_df.bowler.isin(test_season_bowlers)

        selection_options = {
            DataSelectionType.OR_SELECTION: is_test_season_venue | is_test_season_batter | is_test_season_bowler,
            DataSelectionType.AND_SELECTION: is_test_season_venue & is_test_season_batter & is_test_season_bowler
        }
        selection = self.data_selection.get_selection_type()
        train_match_state_df = unqualified_train_match_state_df.loc[selection_options[selection]]

        if calculate_bowling_options:
            logger.debug("Calculating bowling options")

            unqualified_train_bowling_outcomes_df = self.get_bowling_outcomes_by_ball_and_innings(False)
            logger.debug("Applying bowling mask")
            train_bowling_outcomes_df = unqualified_train_bowling_outcomes_df.loc[selection_options[selection]]
        else:
            train_bowling_outcomes_df = pd.DataFrame

        logger.debug("Calculating stats")

        stats = {"Number of balls selected for training": train_match_state_df.shape[0],
                 "Number of balls with bowler in test season bowlers": train_match_state_df. \
                     query('bowler in @test_season_bowlers').shape[0],
                 "Number of balls with batters in test season batters": train_match_state_df. \
                     query('batter in @test_season_bowlers').shape[0],
                 "Number of balls with venues in test season venues": train_match_state_df. \
                     query('venue in @test_season_venues').shape[0]}
        logger.debug("Done with get_match_state_by_balls_for_training")

        logger.debug("Done with get_match_state_by_balls_for_training")
        return train_match_state_df, train_bowling_outcomes_df, stats


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
