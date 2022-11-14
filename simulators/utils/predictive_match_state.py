import random
class MatchState:

    def __init__(self, predictive_utils, scenario_number, match_key, bowling_team, batting_team,
                 batting_playing_xi, bowling_playing_xi):
        self.predictive_utils = predictive_utils
        self.scenario_number = scenario_number
        self.match_key = match_key
        self.bowling_team = bowling_team
        self.batting_team = batting_team
        self.inning = 1
        self.batting_playing_xi = batting_playing_xi
        self.bowling_playing_xi = bowling_playing_xi
        self.available_bowlers = self.bowling_playing_xi.copy()

        self.target_runs = -1
        self.target_balls = -1
        self.initialise_for_innings()

        self.player_label_mapping = {}

        self.update_frequent_players()

        self.match_complete = False
        self.first_innings_complete = False

    def update_state(self, row):
        fielder = ''

        if self.match_complete:
            return fielder

        if self.first_innings_complete and (self.inning == 1):
            return fielder

        is_wicket = row['is_wicket']
        fielder = 'nan'
        self.previous_num_wickets += is_wicket
        if is_wicket == 1:
            dismissal_kind = row['dismissal_kind']
            if dismissal_kind in ['run out', 'caught', 'stumped']:
                list_of_fielders = self.bowling_playing_xi.copy()
                list_of_fielders.remove(self.bowler)
                fielder = random.choice(list_of_fielders)

            non_striker_dismissed = row['non_striker_dismissed']
            if self.previous_num_wickets < 10:
                next_player = self.batting_playing_xi[self.batting_position]
                self.batting_position += 1
                if non_striker_dismissed == 1:
                    self.non_striker = next_player
                else:
                    self.batter = next_player



        batter_runs = row['batter_runs']

        if row['batter_runs'] in [1, 3, 5]:
            non_striker = self.non_striker
            self.non_striker = self.batter
            self.batter = non_striker

        extras = row['extras']
        self.previous_total += batter_runs
        self.previous_total += extras
        self.previous_non_legal_delivery = not row['legal_delivery']

        if self.inning == 2:
            if (self.previous_total >= self.target_runs) or (self.previous_num_wickets == 10):
                self.match_complete = True
                return fielder

        if self.inning == 1:
            if self.previous_num_wickets == 10:
                self.first_innings_complete = True
                return fielder

        return fielder

    def was_previous_non_legal_delivery(self):
        return self.previous_non_legal_delivery

    def update_frequent_players(self):
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
        bowling_order = []
        available_bowlers = self.bowling_playing_xi.copy()
        bowler_map = {}
        previous_bowler = ""
        for i in range(0, 20):
            #bowler = random.choice(available_bowlers)
            bowler = self.predictive_utils.populate_bowler_for_state(self.match_key, self.bowling_team,
                                                                     i, "", available_bowlers)
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
        self.over += 1
        self.ball = 1

        self.bowler = self.bowling_order[self.over]
        self.previous_bowler = self.bowler
        non_striker = self.non_striker
        self.non_striker = self.batter
        self.batter = non_striker

    def bowl_one_ball(self):
        self.ball += 1

    def set_innings(self, inning):
        if self.inning != inning:
            self.inning = inning
            self.target_runs = self.previous_total + 1
            self.target_balls = 20 * 6
            bowling_team = self.bowling_team
            self.bowling_team = self.batting_team
            self.batting_team = bowling_team
            bowling_xi = self.bowling_playing_xi
            self.bowling_playing_xi = self.batting_playing_xi
            self.batting_playing_xi = bowling_xi
            self.available_bowlers = self.bowling_playing_xi.copy()

            self.initialise_for_innings()

    def get_dict_list(self, with_extras=True):
        if self.match_complete or (self.first_innings_complete and (self.inning == 1)):
            return []
        list_to_send = []
        '''if with_extras:
            for item in self.extras_list:
                list_to_send.append(item)
            self.extras_list = []'''

        list_to_send.append({'scenario_number': self.scenario_number,
                             'match_key': self.match_key,
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
                             })

        return list_to_send
