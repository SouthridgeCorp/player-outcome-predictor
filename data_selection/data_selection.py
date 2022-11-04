from historical_data.singleton import Helper
import pandas as pd
from historical_data.playing_xi import PlayingXI


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

    def get_helper(self):
        return self.historical_data_helper

    def get_selected_matches(self, is_testing: bool) -> pd.DataFrame:
        """
        Get all matches from selected tournaments filtered for is_testing
        :param is_testing: Set True if testing data is needed, else set False
        :return: pd.DataFrame listing all matches from selected tournaments in training/testing window
        """
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
        :return: pd.DataFrame listing all playing_xis from matches inselected tournaments in training/testing window
        """
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
        :return: pd.DataFrame listing all balls in all innings from matches inselected tournaments in training/testing
        window
        """

        innings_list = []
        start_date, end_date = self.historical_data_helper.tournaments.get_start_end_dates(is_testing)

        for tournament in self.historical_data_helper.tournaments.get_selected_tournaments():
            matches = self.historical_data_helper.tournaments.matches(tournament)
            match_keys = matches.get_selected_match_keys(start_date, end_date)
            for key in match_keys:
                innings_list.append(self.historical_data_helper.tournaments.innings(tournament).get_innings(key))

        innings_df = pd.concat(innings_list)

        matches_df = self.get_selected_matches(is_testing)
        innings_df = pd.merge(innings_df, matches_df[["key", "team1", "team2"]], left_on="match_key", right_on="key")
        innings_df.drop('key', axis=1, inplace=True)
        innings_df['bowling_team'] = innings_df.apply(lambda x: identify_bowling_team(x), axis=1)

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
            return pd.DataFrame

        df = pd.DataFrame(player_list)

        # Rank the columns
        columns = []
        for team in team_set:
            df[f"{team}_num_matches_played_rank"] = df[f"{team}_num_matches_played"].rank(ascending=False, method="min")
            columns.append(f"{team}_num_matches_played")

        # Calculate featured player
        df = df.assign(best_rank=lambda x: x[columns].min(axis=1))
        df = df.assign(featured_player=lambda x: df['best_rank'] <= 11)
        df = self.merge_with_players(df, 'player_key')
        df.set_index('player_key', inplace=True)
        df = df.sort_values('player_key')

        return df

    def merge_with_players(self, source_df, key, source_left=False):
        return self.historical_data_helper.players.merge_with_players(source_df, key, source_left)

    def get_selected_teams(self, is_testing:bool) -> list:

        start_date, end_date = self.historical_data_helper.tournaments.get_start_end_dates(is_testing)
        selected_teams = []
        for tournament in self.historical_data_helper.tournaments.get_selected_tournaments():
            match = self.historical_data_helper.tournaments.matches(tournament)
            selected_teams += match.get_selected_teams(start_date, end_date)

        return list(set(selected_teams))

    def get_selected_venues(self, is_testing:bool) -> list:

        start_date, end_date = self.historical_data_helper.tournaments.get_start_end_dates(is_testing)
        selected_venues = []
        for tournament in self.historical_data_helper.tournaments.get_selected_tournaments():
            match = self.historical_data_helper.tournaments.matches(tournament)
            selected_venues += match.get_selected_venues(start_date, end_date)

        return list(set(selected_venues))


def identify_bowling_team(row):
    team1 = row["team1"]
    team2 = row["team2"]
    batting_team = row["batting_team"]
    if batting_team == team1:
        return team2
    else:
        return team1