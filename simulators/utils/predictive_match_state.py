import random


class MatchState:
    """
    Class representing the current match state upto the specified inning / over / ball. This is used to build out the
    innings simulation model.
    """
    def __init__(self, predictive_utils, scenario_number, match_key, bowling_team, batting_team,
                 batting_playing_xi, bowling_playing_xi, venue):
        self.predictive_utils = predictive_utils
        self.scenario_number = scenario_number
        self.match_key = match_key
        self.bowling_team = bowling_team
        self.batting_team = batting_team
        self.inning = 1
        self.batting_playing_xi = batting_playing_xi
        self.bowling_playing_xi = bowling_playing_xi
        self.available_bowlers = self.bowling_playing_xi.copy()
        self.venue = venue

        self.target_runs = -1
        self.target_balls = -1
        self.initialise_for_innings()

        self.player_label_mapping = {}

        self.update_frequent_players()

        self.match_complete = False
        self.first_innings_complete = False

    def update_state(self, row):
        """
        This function is called after the outcome of the current ball is known (by the predictive / inferential model).
        This function updates the current state with the outcome of the ball and preps it for the next ball.
        """
        fielder = ''
        if self.match_complete:
            return fielder

        if self.first_innings_complete and (self.inning == 1):
            return fielder

        # Calculate wicket details - count, player dismissed, fielder etc
        is_wicket = row['is_wicket']
        fielder = 'nan'
        self.previous_num_wickets += is_wicket
        if is_wicket == 1:
            dismissal_kind = row['dismissal_kind']
            if dismissal_kind in ['run out', 'caught', 'stumped']:
                # For these dismissal kinds, choose a random fielder from the bowling team (except the bowler)
                list_of_fielders = self.bowling_playing_xi.copy()
                list_of_fielders.remove(self.bowler)
                fielder = random.choice(list_of_fielders)

            # Identify the next batter who will replace the player dismissed (either batter or non_striker)
            non_striker_dismissed = row['non_striker_dismissed']
            if self.previous_num_wickets < 10:
                next_player = self.batting_playing_xi[self.batting_position]
                self.batting_position += 1
                if non_striker_dismissed == 1:
                    self.non_striker = next_player
                else:
                    self.batter = next_player

        batter_runs = row['batter_runs']

        # Swap batter / non_striker for odd runs
        if row['batter_runs'] in [1, 3, 5]:
            non_striker = self.non_striker
            self.non_striker = self.batter
            self.batter = non_striker

        # Calculate the total runs scored
        extras = row['extras']
        self.previous_total += batter_runs
        self.previous_total += extras

        # Set the legality of the previous delivery
        self.previous_non_legal_delivery = not row['legal_delivery']

        # Check if the match is complete..
        if self.inning == 2:
            #.. either the team batting second met the target or they ran out of wickets (inning / over count is
            # managed outside the context of this match state).
            if (self.previous_total >= self.target_runs) or (self.previous_num_wickets == 10):
                self.match_complete = True
                return fielder

        # Check if the first innings is complete because the team is bowled out. (inning / over count is
        # managed outside the context of this match state.
        if self.inning == 1:
            if self.previous_num_wickets == 10:
                self.first_innings_complete = True
                return fielder

        return fielder

    def was_previous_non_legal_delivery(self):
        """
        Getter for checking if the previous delivery was not legal
        """
        return self.previous_non_legal_delivery

    def update_frequent_players(self):
        """
        Maintain a mapping of the frequent players labels which are used to build out the dictionary
        """
        featured_players = self.predictive_utils.featured_player_df[
            self.predictive_utils.featured_player_df.index.isin(self.bowling_playing_xi + self.batting_playing_xi)]

        for player in self.bowling_playing_xi + self.batting_playing_xi:
            if featured_players.loc[player]['featured_player']:
                self.player_label_mapping[player] = player
            else:
                self.player_label_mapping[player] = "non_frequent_player"

    def initialise_for_innings(self):
        self.over = -1
        self.ball = 1
        self.previous_total = 0
        self.previous_num_wickets = 0
        self.bowler = ""
        self.batting_position = 0
        self.batter = self.batting_playing_xi[self.batting_position + 1]
        self.non_striker = self.batting_playing_xi[self.batting_position]
        self.bowling_order = self.setup_bowler_per_over()
        self.batting_position = 2
        self.bowler_map = {}
        self.previous_bowler = ""
        self.previous_non_legal_delivery = False

    def setup_bowler_per_over(self):
        """
        Decide on the bowling playing xi before the match starts
        """

        #TODO: Assess if this logic should just be applied per over instead of in one go on initialisation & inning
        # change due to perf considerations
        bowling_order = []
        available_bowlers = self.bowling_playing_xi.copy()
        bowler_map = {}
        previous_bowler = ""
        for i in range(0, 20):
            bowler = self.predictive_utils.populate_bowler_for_state(self.match_key, self.bowling_team,
                                                                     i, previous_bowler, available_bowlers)
            bowling_order.append(bowler)
            previous_bowler = bowler
            if bowler in bowler_map.keys():
                bowler_map[bowler] += 1
            else:
                bowler_map[bowler] = 1

            if bowler_map[bowler] == 4:
                available_bowlers.remove(bowler)

        return bowling_order

    def change_over(self):
        """
        Step up the over number, find a new bowler, swap the batter & non-striker and set ball count = 1
        """
        self.over += 1
        self.ball = 1

        self.bowler = self.bowling_order[self.over]
        self.previous_bowler = self.bowler

        non_striker = self.non_striker
        self.non_striker = self.batter
        self.batter = non_striker

    def bowl_one_ball(self):
        """
        Progress ball count by 1 in the same over
        """
        self.ball += 1

    def set_innings(self, inning):
        """
        Switch innings from 1 to 2
        """
        if self.inning != inning:
            self.inning = inning
            # Set target details for the 2nd innings
            self.target_runs = self.previous_total + 1
            self.target_balls = 20 * 6

            # Swap the batting & bowling teams
            bowling_team = self.bowling_team
            self.bowling_team = self.batting_team
            self.batting_team = bowling_team
            bowling_xi = self.bowling_playing_xi
            self.bowling_playing_xi = self.batting_playing_xi
            self.batting_playing_xi = bowling_xi

            # Prep for the new bowling xi
            self.available_bowlers = self.bowling_playing_xi.copy()

            self.initialise_for_innings()

    def get_dict(self):
        """
        For an active match, returns a dictionary representing the current state. Returns an empty dict for completed
        matches / innings
        """
        if self.match_complete or (self.first_innings_complete and (self.inning == 1)):
            return {}

        return {'scenario_number': self.scenario_number,
                'match_key': self.match_key,
                'venue': self.venue,
                'bowling_team': self.bowling_team,
                'batting_team': self.batting_team,
                'inning': self.inning,
                'over': self.over,
                'ball': self.ball,
                'previous_total': self.previous_total,
                'previous_number_of_wickets': self.previous_num_wickets,
                'bowler': self.player_label_mapping[self.bowler],
                'batter': self.player_label_mapping[self.batter],
                'non_striker': self.player_label_mapping[self.non_striker],
                'target_runs': self.target_runs,
                'target_balls': self.target_balls
                }
