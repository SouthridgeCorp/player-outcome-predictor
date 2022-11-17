from historical_data.singleton import Helper
import pandas as pd
from historical_data.playing_xi import PlayingXI
import logging

import warnings
warnings.filterwarnings('ignore')

class PlayerInformation:
    """
    Helper class - do not use outside this context - used to keep count of all the matches per team played by a player
    """

    def __init__(self, player_key):
        self.player_key = player_key
        self.match_count = {}

    def get_match_count(self, team):
        if team not in self.match_count.keys():
            self.match_count[team] = 0
        return self.match_count[team]

    def increment_match_count(self, team):
        if team not in self.match_count.keys():
            self.match_count[team] = 0
        self.match_count[team] += 1

    def get_dictionary(self):
        player_dict = {"player_key": self.player_key}
        for key in self.match_count.keys():
            player_dict[f"{key}_num_matches_played"] = self.match_count[key]

        return player_dict


class DataSelection:

    def __init__(self,
                 historical_data_helper: Helper):
        self.historical_data_helper = historical_data_helper

        # placeholders for storing simulated data - if not defined, historical data will be used
        self.simulated_matches = pd.DataFrame()
        self.simulated_innings = pd.DataFrame()
        self.simulated_playing_xi = pd.DataFrame()

    def get_helper(self) -> Helper:
        """
        Returns the underlying Helper object
        :return: Helper instance
        """
        return self.historical_data_helper

    def set_simulated_data(self, matches_df: pd.DataFrame=pd.DataFrame(),
                           innings_df: pd.DataFrame=pd.DataFrame(),
                           playing_xi_df: pd.DataFrame=pd.DataFrame()):
        """
        Sets the simulated datasets to be used by this object
        :param matches_df: the simulated matches object
        :param innings_df: the simulated innings object
        :param playing_xi_df: the simulated playing_xi object
        :return None
        """
        self.simulated_matches = matches_df
        self.simulated_innings = innings_df
        self.simulated_playing_xi = playing_xi_df

    def get_selected_matches(self, is_testing: bool) -> pd.DataFrame:
        """
        Get all matches from selected tournaments filtered for is_testing
        :param is_testing: Set True if testing data is needed, else set False
        :return: pd.DataFrame listing all matches from selected tournaments in training/testing window
        """

        # Return simulated matches if available
        if is_testing and not self.simulated_matches.empty:
            return self.simulated_matches

        start_date, end_date = self.historical_data_helper.tournaments.get_start_end_dates(is_testing)

        selected_matches_list = []
        for tournament in self.historical_data_helper.tournaments.get_selected_tournaments():
            matches = self.historical_data_helper.tournaments.matches(tournament).get_selected_matches(start_date,
                                                                                                       end_date)
            selected_matches_list.append(matches)

        selected_matches_df = pd.concat(selected_matches_list)

        return selected_matches_df

    def get_playing_xi_for_selected_matches(self, is_testing: bool) -> pd.DataFrame:
        """
        Get all playing_xis from matches in selected tournaments filtered for is_testing
        :param is_testing: Set True if testing data is needed, else set False
        :return: pd.DataFrame listing all playing_xis from matches in selected tournaments in training/testing window
        """

        # Return simulated matches if available
        if is_testing and not self.simulated_playing_xi.empty:
            return self.simulated_playing_xi

        playing_xi_list = []
        start_date, end_date = self.historical_data_helper.tournaments.get_start_end_dates(is_testing)

        for tournament in self.historical_data_helper.tournaments.get_selected_tournaments():
            matches = self.historical_data_helper.tournaments.matches(tournament)
            match_keys = matches.get_selected_match_keys(start_date, end_date)
            for key in match_keys:
                team1, team2 = matches.get_teams(key)
                playing_xi_list.append(
                    self.historical_data_helper.tournaments.playing_xi(tournament).get_playing_xi(key, team1))
                playing_xi_list.append(
                    self.historical_data_helper.tournaments.playing_xi(tournament).get_playing_xi(key, team2))

        if len(playing_xi_list) > 0:
            playing_xi_df = pd.concat(playing_xi_list)
        else:
            playing_xi_df = pd.DataFrame()
        return playing_xi_df

    def get_innings_for_selected_matches(self, is_testing: bool) -> pd.DataFrame:
        """
        Get ball_by_ball pre-processed innings data from matches in selected tournaments filtered for is_testing
        :param is_testing: Set True if testing data is needed, else set False
        :return: pd.DataFrame listing all balls in all innings from matches in selected tournaments in training/testing
        window
        """

        # Return simulated innings if available
        if is_testing and not self.simulated_innings.empty:
            return self.simulated_innings

        innings_list = []
        start_date, end_date = self.historical_data_helper.tournaments.get_start_end_dates(is_testing)

        for tournament in self.historical_data_helper.tournaments.get_selected_tournaments():
            matches = self.historical_data_helper.tournaments.matches(tournament)
            match_keys = matches.get_selected_match_keys(start_date, end_date)
            innings_list.append(self.historical_data_helper.tournaments.innings(tournament).
                                get_innings_from_match_list(match_keys))

        innings_df = pd.concat(innings_list)

        matches_df = self.get_selected_matches(is_testing)
        innings_df = pd.merge(innings_df, matches_df[["key", "team1", "team2"]], left_on="match_key", right_on="key")
        innings_df.drop('key', axis=1, inplace=True)

        innings_df['bowling_team'] = innings_df['team1']
        mask = innings_df['team1'] == innings_df['batting_team']
        innings_df.loc[mask, 'bowling_team'] = innings_df['team2']

        return innings_df

    def get_frequent_players_universe(self) -> pd.DataFrame:
        """
        Returns a dataframe representing whether a player is featured frequently in a team or not in the training window
        df schema:
            index: [player_key]
            columns: [
                {team_key}_num_matches_played : number of matches played by the player for the team in the training
                window
                {team_key}_num_matches_played_rank : rank of the player key in terms of number of matches played for
                the team
                featured_player: 1 if player has rank <= 11 for at least 1 team, else zero
                best_rank: The best rank the player has achieved across all teams they have played for
                ]
        :return: pd.DataFrame as above
        """
        playing_xi_df = self.get_playing_xi_for_selected_matches(is_testing=False)

        playing_xi_list = playing_xi_df.to_dict('records')  # Get the entire playing xi information

        # ******** Calculate the match count per team per player ******************

        # Map all the information available by players
        player_info_dict = {}
        # Keep track of all teams seen
        team_set = set()
        # for each player & team in the xi
        for row in playing_xi_list:
            player_key = row[PlayingXI.PLAYER_KEY_COLUMN]
            team_key = row[PlayingXI.TEAM_COLUMN]

            if player_key not in player_info_dict.keys():
                player_info_dict[player_key] = PlayerInformation(player_key)

            # increment the match count for the player & team
            player_info_dict[player_key].increment_match_count(team_key)
            team_set.add(team_key)

        # *************** Populate the dataframe *******************
        player_list = []
        for player_key in player_info_dict.keys():
            player_list.append(player_info_dict[player_key].get_dictionary())

        if len(player_list) == 0:
            return pd.DataFrame()

        df = pd.DataFrame(player_list)

        # Rank the columns
        columns = []
        for team in team_set:
            df[f"{team}_num_matches_played"] = df[f"{team}_num_matches_played"].fillna(0)
            df[f"{team}_num_matches_played"] = df[f"{team}_num_matches_played"].astype(int)
            df[f"{team}_num_matches_played_rank"] = df[f"{team}_num_matches_played"].rank(ascending=False, method="min")
            columns.append(f"{team}_num_matches_played_rank")

        # Calculate featured player
        df = df.assign(best_rank=lambda x: x[columns].min(axis=1))
        df = df.assign(featured_player=lambda x: df['best_rank'] <= 11)
        df = self.merge_with_players(df, 'player_key')
        df.set_index('player_key', inplace=True)
        df = df.sort_values('player_key')

        return df

    def merge_with_players(self, source_df: pd.DataFrame, key: str, source_left: bool = False) -> pd.DataFrame:
        """
        Merges the provided dataframe with the players_df
        :param source_df The dataframe to be merged with players
        :param key The key for the source df
        :param source_left merge left vs right
        :return The merged dataframe
        """
        return self.historical_data_helper.players.merge_with_players(source_df, key, source_left)

    def get_selected_teams(self, is_testing: bool) -> list:
        """
        Get a list of selected teams from the underlying helper
        """
        start_date, end_date = self.historical_data_helper.tournaments.get_start_end_dates(is_testing)
        selected_teams = []
        for tournament in self.historical_data_helper.tournaments.get_selected_tournaments():
            match = self.historical_data_helper.tournaments.matches(tournament)
            selected_teams += match.get_selected_teams(start_date, end_date)

        return list(set(selected_teams))

    def get_selected_venues(self, is_testing: bool) -> list:
        """
        Get a list of selected venues from the underlying helper
        """
        start_date, end_date = self.historical_data_helper.tournaments.get_start_end_dates(is_testing)
        selected_venues = []
        for tournament in self.historical_data_helper.tournaments.get_selected_tournaments():
            match = self.historical_data_helper.tournaments.matches(tournament)
            selected_venues += match.get_selected_venues(start_date, end_date)

        return list(set(selected_venues))

    def get_all_matches(self) -> pd.DataFrame:
        """
        Get all matches that the tournaments object knows about
        :return: pd.DataFrame listing all the matches information avaialble
        """
        return self.historical_data_helper.tournaments.get_all_matches()

    def get_all_innings_and_matches(self) -> (pd.DataFrame, pd.DataFrame):
        """
        Get all matches & innings that the tournaments object knows about
        :return: 2 dataframes, first one containing matches and second one containing innings information
        """
        matches_df, innings_df = self.historical_data_helper.tournaments.get_all_matches_and_innings_cached()

        innings_df = pd.merge(innings_df, matches_df[["key", "team1", "team2"]], left_on="match_key", right_on="key")
        innings_df.drop('key', axis=1, inplace=True)

        innings_df['bowling_team'] = innings_df['team1']
        mask = innings_df['team1'] == innings_df['batting_team']
        innings_df.loc[mask, 'bowling_team'] = innings_df['team2']

        innings_df.drop(['team1', 'team2'], axis=1, inplace=True)

        return innings_df, matches_df

    def get_all_players(self) -> pd.DataFrame:
        """
        Get all players that we know about
        :return: pd.DataFrame listing all the player information available
        """
        return self.historical_data_helper.players.get_players()
