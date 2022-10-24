from historical_data.singleton import Helper
import pandas as pd

class DataSelection:

    def __init__(self,
                 historical_data_helper:Helper):
        self.historical_data_helper = historical_data_helper

    def get_selected_matches(self,
                             is_testing:bool)-> pd.DataFrame:
        """
        Get all matches from selected tournaments filtered for is_testing
        :param is_testing: Set True if testing data is needed, else set False
        :return: pd.DataFrame listing all matches from selected tournaments in training/testing window
        """
        if is_testing:
            start_date = self.historical_data_helper.tournaments.testing_start
            end_date = self.historical_data_helper.tournaments.testing_end
        else:
            start_date = self.historical_data_helper.tournaments.training_start
            end_date = self.historical_data_helper.tournaments.training_end

        selected_matches_list = []
        for tournament in self.historical_data_helper.tournaments.selected:
            matches = self.historical_data_helper.tournaments.matches(tournament).get_selected_matches(start_date,
                                                                                                       end_date)
            selected_matches_list.append(matches)

        selected_matches_df = pd.concat(selected_matches_list)

        return selected_matches_df

    def get_playing_xi_for_selected_matches(self,
                                            is_testing:bool)->pd.DataFrame:
        """
        Get all playing_xis from matches in selected tournaments filtered for is_testing
        :param is_testing: Set True if testing data is needed, else set False
        :return: pd.DataFrame listing all playing_xis from matches inselected tournaments in training/testing window
        """
        #TODO: Implement this
        return pd.DataFrame()

    def get_innings_for_selected_matches(self,
                                         is_testing:bool)->pd.DataFrame:
        """
        Get ball_by_ball pre-processed innings data from matches in selected tournaments filtered for is_testing
        :param is_testing: Set True if testing data is needed, else set False
        :return: pd.DataFrame listing all balls in all innings from matches inselected tournaments in training/testing
        window
        """
        #TODO: Implement this
        return pd.DataFrame()

    def get_frequent_players_universe(self)-> pd.DataFrame:
        """
        Returns a dataframe representing whether a player is featured frequently in a team or not in the training window
        df schema:
            index: [player_key]
            columns: [
                {team_key}_num_matches_played : number of matches played by the player for the team in the training window
                {team_key}_num_matches_played_rank : rank of the player key in terms of number of matches played for the team
                featured_player: 1 if player has rank <= 11 for at least 1 team, else zero
                ]
        :return: pd.DataFrame as above
        """
        #TODO: implement this.
        return pd.DataFrame()