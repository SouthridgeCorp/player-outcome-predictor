from data_selection.data_selection import DataSelection
import pandas as pd

class PerfectSimulator:

    def __init__(self,
                 data_selection:DataSelection):
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
            index: [match_key, innings, over_number, ball_number]
            columns: bowling_outcomes_index
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