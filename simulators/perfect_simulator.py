from data_selection.data_selection import DataSelection
from rewards_configuration.rewards_configuration import RewardsConfiguration
import pandas as pd

class PerfectSimulator:

    def __init__(self,
                 data_selection:DataSelection,
                 rewards_configuration:RewardsConfiguration):
        self.data_selection = data_selection

    def get_bowling_outcomes_by_ball_and_innings(self,
                                                 is_testing:bool)-> pd.DataFrame:
        """
        Returns a dataframe with bowling outcomes by ball and innings mapped as below:
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
        df schema:
            index: [match_key, innings, over_number, ball_number, bowler]
            columns: bowling_outcomes_index, bowler_id
            values: [one of 0, 1-b, 1-oe, 1-nb, 1-w,  2-b…. 6-b, 6-oe, 6-nb, 6-w, W-b, W-nb]

        :param is_testing: Set True if testing data is needed, else set False
        :return: pd.DataFrame listing bowling outcomes for each ball in each innings in training/testing matches for
        selected tournaments
        """
        #TODO: Implement this
        return pd.DataFrame()

    def get_match_state_by_ball_and_innings(self,
                                            is_testing:bool)-> pd.DataFrame:
        """
        Returns a dataframe representing the state of the match before a given ball in a given innings was bowled:
        df schema:
            index: [match_key, innings, over_number, ball_number]
            columns:
                [
                - `batter_{id}` (one-hot encoded on the universe of top 11 most frequently featured players in each team
                + 1 column for not_frequent_player i.e if the batsman_id is a player who is not one of the top 11 most
                frequently featured players, then we should get a 1 in in the 'not_frequent_player' column. The effect
                of this is to limit the total number of columns to no more than (num_teams*11) + 1
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
        #TODO: Implement this. Refer to https://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.LabelBinarizer.html
        return pd.DataFrame()

    def get_batting_outcomes_by_ball_and_innings(self,
                                                 is_testing:bool)-> pd.DataFrame:
        """
        Returns a dataframe representing mutually exclusive outcomes for a batter, composed of
        - [0, 1-b, 2-b, 3-b, 4-b, 5-b, 6-b, W]
        - 0 : dot_ball, and other bowling_outcomes not attributable to batsman, excluding wickets
        - 1-b: same as 1-b bowling_outcome
        - ... for upto 6 runs
        - W: union of W-b, W-bc, W-bs, W-dro, W-idro, W-others from bowling_outcome
        df schema:
            index: [match_key, innings, over_number, ball_number]
            columns: batting_outcomes_index, batter_id
            values: [one of 0, 1-b, 2-b, 3-b, 4-b, 5-b, 6-b, W]

        :param is_testing: Set True if testing data is needed, else set False
        :return: pd.DataFrame listing batting outcomes for each ball in each innings in training/testing matches for
        selected tournaments
        """
        #TODO: Implement this by passing self.get_bowling_outcomes_by_ball_and_innings and a batter_id df to a
        # simulator.utils.bowling_to_batting_outcomes_converter function which implements the core logic as a function
        # call rather than a class method. This function can be used by other classes/methods which have access to an
        # appropriate bowling_outcomes_index column.
        return pd.DataFrame()

    def get_fielding_outcomes_by_ball_and_innings(self,
                                                 is_testing:bool)-> pd.DataFrame:
        """
        Returns a dataframe representing mutually exclusive outcomes for a fielder, composed of
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
        :return: pd.DataFrame listing fielding outcomes for each ball in each innings in training/testing matches for
        selected tournaments
        """
        #TODO: Implement this by passing self.get_bowling_outcomes_by_ball_and_innings and a fielder_id df to a
        # simulator.utils.bowling_to_fielding_outcomes_converter function which implements the core logic as a function
        # call rather than a class method. This function can be used by other classes/methods which have access to an
        # appropriate bowling_outcomes_index column.
        return pd.DataFrame()

    def get_outcomes_by_ball_and_innings(self,
                                         is_testing:bool)->pd.DataFrame:
        """Returns a dataframe representing all outcomes at a ball and innings level for the train/test dataset
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
        :return: pd.DataFrame as above"""
        #TODO: implement this
        return pd.DataFrame()

    def get_outcomes_by_player_and_innings(self,
                                           is_testing:bool)-> pd.DataFrame:
        """Returns a dataframe representing all outcomes at a player and innings level for the train/test dataset
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
        #TODO: implement this
        return pd.DataFrame()

    def get_outcomes_by_team_and_innings(self,
                                         is_testing:bool)-> pd.DataFrame:
        """Returns a dataframe representing all outcomes at a player and innings level for the train/test dataset
        df schema:
            index: [match_key, innings, team_id]
            columns: [
                    bowling_economy_rate,
                    batting_strike_rate
                    ]
        See `outcomes_by_team_and_innings` subgraph of the computational model
        :param is_testing: Set True if testing data is needed, else set False
        :return: pd.DataFrame as above"""
        #TODO: implement this
        return pd.DataFrame()

    def get_rewards_components(self,
                               is_testing:bool)->(pd.DataFrame,pd.DataFrame):
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
                    bowling_bonus,
                    bowling_penalty,
                    batting_bonus,
                    batting_penalty
                    ]
        See `rewards` subgraph of the computational model
        :param is_testing: Set True if testing data is needed, else set False
        :return: pd.DataFrame as above"""
        #TODO: implement this
        return pd.DataFrame()

    def get_simulation_evaluation_metrics_by_granularity(self,
                                                         is_testing:bool,
                                                         granularity:str)->pd.DataFrame:
        """Returns a dataframe representing all rewards for a player at the chosen granularity level:
        df schema:
            index: [player_key,
                    granluarity_key - depends on the granularity param, if innings (tournament_key, tournament_stage, match_key, innings), else
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
        :return: pd.DataFrame as above"""
        #TODO: implement this
        return pd.DataFrame()

    def get_error_measures(self,
                           is_testing:bool,
                           contender_simulation_evaluation_metrics:pd.DataFrame)->pd.DataFrame:
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
        :return: pd.DataFrame as above
        :raises: Exception if the contender_simulation_evaluation_metrics does not have a matching index
        to the result of self.get_simulation_evaluation_metrics(is_testing,granularity [as implied by the contender df]"""
        #TODO: implement this
        return pd.DataFrame()