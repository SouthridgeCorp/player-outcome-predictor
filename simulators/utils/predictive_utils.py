import scipy.stats as sps
import pandas as pd
import numpy as np
from data_selection.data_selection import DataSelection
import logging

from inferential_models.batter_runs_models import BatterRunsModel


def calculate_bowling_probabilities(all_innings_df) -> pd.DataFrame:
    """
    Counts the number of matches bowled by a player for a specific team & over, and uses that frequency as the
    probability distribution to seed the multinomial distribution to predict if a certain over for a certain team is
    bowled by a certain bowler.
    """
    frequencies_df = \
        all_innings_df.groupby(['bowling_team', 'over', 'bowler']).count()['match_key'].unstack()

    frequencies_df = frequencies_df.fillna(0)
    frequencies_df = frequencies_df.astype('float64')

    bowling_probabilities = Probabilities()
    bowling_probabilities.populate_labels(frequencies_df.columns.values.tolist())

    # Note: This entire operation could have been done via DataFrames but it led to precision errors with
    # sps, hence np is used instead.
    for index, row in frequencies_df.iterrows():
        array = row.values.tolist()
        a = np.asarray(array).astype('float64')
        a = a / np.sum(a)
        if np.sum(a) > 1.0:
            a[np.argmax(a)] += 1.0 - np.sum(a)

        bowling_probabilities.setup_probability(index, a)

    bowling_probabilities.setup_multinomials()

    return bowling_probabilities


class Probabilities:
    """
    Helper class to maintain and store probability details. This is especially useful for multinomial distributions
    where pd.DataFrame calculations may yield floating point errors and hence calculations need to be done via numpy
    instead.
    Must not be used outside the context of the PredictiveUtils class since the logic is tightly coupled.
    """

    def __init__(self):
        # The labels associated with each probability, must be in lock step with the array of probabilities included in
        # probability_map
        self.label_list = []
        # Map containing a list of probabilities for each key - each item in the list maps to a label in label_list
        self.probability_map = {}
        # A map of multinomial instances mapped to the same key as the probability map
        self.multinomial_map = {}

    def populate_labels(self, labels):
        self.label_list = labels

    def setup_probability(self, key, probabilities):
        self.probability_map[key] = probabilities

    def get_probability(self, key):
        return self.probability_map[key]

    def get_label(self, id):
        return self.label_list[id]

    def isin(self, key):
        return key in self.probability_map.keys()

    def setup_multinomials(self):
        for key in self.probability_map.keys():
            multinomial = sps.multinomial(1, self.get_probability(key))
            self.multinomial_map[key] = multinomial

    def get_multinomial(self, key):
        return self.multinomial_map[key]


class PredictiveUtils:
    def __init__(self,
                 data_selection: DataSelection,
                 batter_runs_model: BatterRunsModel):
        self.data_selection = data_selection
        self.all_innings_df = pd.DataFrame()
        self.all_matches_df = pd.DataFrame()
        self.bowling_probabilities = Probabilities()
        self.featured_player_df = pd.DataFrame()
        self.batter_runs_model = batter_runs_model

        self.batter_runs_model.initiate_model(session_type='testing')

        logging.debug("setting up distributions")
        # TODO: These distributions will no longer be required once the inferential model comes into play.

        # Probability of a legal delivery
        self.legal_delivery_distribution = sps.bernoulli(p=0.9)

        # Probability distribution of batting runs on a legal, wicket-less delivery
        legal_batting_distribution = [0.4, 0.35, 0.075, 0.006, 0.125, 0.004, 0.04]
        self.batter_runs_distribution = sps.multinomial(1, legal_batting_distribution)

        # Probability of getting an extra if there are no batter runs
        self.extras_if_legal_no_run_distribution = sps.bernoulli(p=.03)

        # Probability of wickets on a legal delivery
        self.legal_wickets_distribution = sps.bernoulli(p=.05)

        # Probability distribution of dismissal kinds
        self.legal_wicket_types = ["caught", "bowled", "run out", "lbw", "caught and bowled", "stumped", "others"]
        legal_wicket_types_distribution_list = [0.6, 0.19, 0.08, 0.07, 0.03, 0.03, 0.06]
        self.legal_wicket_types_distribution = sps.multinomial(1, legal_wicket_types_distribution_list)

        # Probability of a single if a wicket was lost
        # ASSUMPTION: If there was a wicket, at the most 1 batter run could be scored
        self.legal_wicket_single_distribution = sps.bernoulli(p=0.03)

        # Probability of a run out being a runout
        self.direct_run_out_probability = sps.bernoulli(p=0.5)

        # Probability of a non striker being dismissed on a runout
        self.non_striker_dismissed_on_runout = sps.bernoulli(p=0.5)

        # Distribution of non-legal deliveries
        self.non_legal_deliveries = ["wides", "noballs"]
        non_legal_deliveries_probability = [0.87, 0.13]
        self.non_legal_deliveries_distribution = sps.multinomial(1, non_legal_deliveries_probability)

        # Distribution of extras scored on a non-legal delivery
        non_legal_extras_probability = [0, 0.89, 0.07, 0.01, 0.001, 0.03]
        self.non_legal_extras_distribution = sps.multinomial(1, non_legal_extras_probability)

        # Distribution of batter runs scored on a non-legal delivery
        non_legal_batter_runs_probability = [0.93, 0.03, 0.008, 0, 0.014, 0, 0.008]
        self.non_legal_batter_runs_distribution = sps.multinomial(1, non_legal_batter_runs_probability)

        # Probability of a wicket on a non-legal delivery
        self.non_legal_wickets_distribution = sps.bernoulli(p=.0099)

        # Distribution of dismissal kind on a non-legal wicket
        self.non_legal_wicket_types = ["stumped", "run out"]
        non_legal_wicket_types_distribution_list = [0.65, 0.35]
        self.non_legal_wicket_types_distribution = sps.multinomial(1, non_legal_wicket_types_distribution_list)

        # Probability of a single batter_run on a non-legal wicket
        self.non_legal_wicket_single_distribution = sps.bernoulli(p=0.03)

        # Probability of an extra on a non-legal wicket
        non_legal_wicket_extras_probability = [0, 0.97, 0.024, 0, 0.001, 0.006]
        self.non_legal_wicket_extras_distribution = sps.multinomial(1, non_legal_wicket_extras_probability)

        self.is_setup = False

    def predict_runout_details(self, matches_df, base_mask):
        """
        Predicts direct / indirect runouts and which player got dismissed. Updates matches_df directly with the details.
        """
        matches_df.loc[base_mask, 'player_dismissed'] = matches_df['batter']

        base_mask = base_mask & (matches_df['dismissal_kind'] == 'run out')
        number_of_balls = len(base_mask[base_mask])
        if number_of_balls > 0:
            matches_df.loc[base_mask, 'is_direct_runout'] = self.direct_run_out_probability.rvs(number_of_balls)
            matches_df.loc[base_mask, 'non_striker_dismissed'] \
                = self.non_striker_dismissed_on_runout.rvs(number_of_balls)

        base_mask = base_mask & (matches_df['non_striker_dismissed'] == 1)
        matches_df.loc[base_mask, 'player_dismissed'] = matches_df['non_striker']

    def predict_legal_wickets(self, matches_df):
        """
        Predicts when wickets fall for a legal delivery, the dismissal kind and runs scored.
        Updates matches_df directly with the details.
        """
        # Set up details for legal delivery
        mask = matches_df['legal_delivery']
        number_of_balls = len(mask[mask])

        # setup legal wicket scenarios
        matches_df.loc[mask, 'is_wicket'] = self.legal_wickets_distribution.rvs(number_of_balls)

        wicket_mask = mask & (matches_df['is_wicket'] == 1)
        number_of_balls = len(wicket_mask[wicket_mask])
        dismissal_kind = self.legal_wicket_types_distribution.rvs(number_of_balls)
        indices = np.where(dismissal_kind == 1)[1]
        assert (len(indices) == number_of_balls)

        matches_df.loc[wicket_mask, 'dismissal_kind'] = [self.legal_wicket_types[i] for i in indices]
        matches_df.loc[wicket_mask, 'batter_runs'] = self.legal_wicket_single_distribution.rvs(number_of_balls)

        self.predict_runout_details(matches_df, wicket_mask)

    def predict_legal_outcomes(self,
                               matches_df,
                               use_inferential_model):
        """
        Predicts outcomes on a legal delivery, including batter_runs, extras and wickets
        Updates matches_df directly with the details.
        """
        # Set up details for legal delivery
        mask = matches_df['legal_delivery']

        self.predict_legal_wickets(matches_df)

        # Setup legal non-wicket scenarios
        mask = mask & (matches_df['is_wicket'] == 0)
        number_of_balls = len(mask[mask])

        # Set up legal delivery batting runs

        if not use_inferential_model:
            batting_runs = self.batter_runs_distribution.rvs(number_of_balls)
            matches_df.loc[mask, 'batter_runs'] = np.where(batting_runs == 1)[1]
        else:
            match_state_df = matches_df.loc[mask]
            if not(match_state_df.empty):
                inferred_batting_runs = self.batter_runs_model.get_batter_runs_given_match_state(match_state_df)
                matches_df.loc[mask, 'batter_runs'] = inferred_batting_runs['batter_runs'].values
            else:
                logging.debug("Got empty match state df, bypassing inferential model")

        # set up extras for legal deliveries
        extras_mask = mask & (matches_df['batter_runs'] == 0)
        number_of_balls = len(extras_mask[extras_mask])
        matches_df.loc[extras_mask, 'extras'] = self.extras_if_legal_no_run_distribution.rvs(number_of_balls)

    def predict_non_legal_wicket_outcomes(self, matches_df):
        """
        Predicts the probability of a wicket on a non-legal delivery and sets its corresponding outcomes
        Updates matches_df directly with the details.
        """
        # Set up details for legal delivery
        mask = ~matches_df['legal_delivery']
        number_of_balls = len(mask[mask])

        # setup legal wicket scenarios
        matches_df.loc[mask, 'is_wicket'] = self.non_legal_wickets_distribution.rvs(number_of_balls)

        wicket_mask = mask & (matches_df['is_wicket'] == 1)
        number_of_balls = len(wicket_mask[wicket_mask])
        dismissal_kind = self.non_legal_wicket_types_distribution.rvs(number_of_balls)
        indices = np.where(dismissal_kind == 1)[1]
        assert (len(indices) == number_of_balls)

        matches_df.loc[wicket_mask, 'dismissal_kind'] = [self.non_legal_wicket_types[i] for i in indices]
        matches_df.loc[wicket_mask, 'batter_runs'] = self.non_legal_wicket_single_distribution.rvs(number_of_balls)

        # set up extras for non-legal wickets
        extras = self.non_legal_wicket_extras_distribution.rvs(number_of_balls)
        matches_df.loc[wicket_mask, 'extras'] = np.where(extras == 1)[1]

        self.predict_runout_details(matches_df, wicket_mask)

    def predict_non_legal_outcomes(self, matches_df):
        """
        Predicts outcomes on a legal delivery, including batter_runs, extras and wickets
        """
        mask = ~matches_df['legal_delivery']

        number_of_balls = len(mask[mask])
        non_legal_delivery = self.non_legal_deliveries_distribution.rvs(number_of_balls)
        indices = np.where(non_legal_delivery == 1)[1]
        assert (len(indices) == number_of_balls)

        matches_df.loc[mask, "wides"] = [1 if i == 0 else 0 for i in indices]
        matches_df.loc[mask, "noballs"] = [1 if i == 1 else 0 for i in indices]

        self.predict_non_legal_wicket_outcomes(matches_df)

        # Predict extras for non-legal deliveries
        mask = mask & (matches_df['is_wicket'] == 0)
        number_of_balls = len(mask[mask])

        # Set up non-legal delivery extra runs
        extra_runs = self.non_legal_extras_distribution.rvs(number_of_balls)
        matches_df.loc[mask, 'extras'] = np.where(extra_runs == 1)[1]

        # Set up non-legal delivery batter runs
        batter_runs = self.non_legal_batter_runs_distribution.rvs(number_of_balls)
        matches_df.loc[mask, 'batter_runs'] = np.where(batter_runs == 1)[1]

    def predict_ball_by_ball_outcome(self,
                                     matches_df,
                                     use_inferential_model):
        """
        This function assumes that the matches_df represents the current state of the match up until the specified
        ball is bowled, and then predicts the outcome of the current delivery.
        matches_df must contain one row per match, representing a summary of the current match state.
        """
        match_count = len(matches_df.index)

        is_legal_delivery = self.legal_delivery_distribution.rvs(match_count,
                                                                 random_state=np.random.randint(low=3)) == 1
        # Setup defaults before predicting specific
        matches_df['legal_delivery'] = is_legal_delivery

        matches_df['batter_runs'] = 0
        matches_df['extras'] = 0
        matches_df['is_wicket'] = 0
        matches_df['dismissal_kind'] = 'nan'
        matches_df['non_striker_dismissed'] = 0
        matches_df['player_dismissed'] = 'nan'
        matches_df['is_direct_runout'] = 0
        matches_df['noballs'] = 0
        matches_df['wides'] = 0

        self.predict_legal_outcomes(matches_df,
                                    use_inferential_model)
        self.predict_non_legal_outcomes(matches_df)

    def setup(self):
        """
        Initial setup required for generating scenarios
        """

        if self.is_setup:
            logging.debug("Utils is already setup - not setting up again")
            return

        logging.debug("getting all innings and matches")
        self.all_innings_df, self.all_matches_df = self.data_selection.get_all_innings_and_matches()

        logging.debug("Calculating bowling probabilities")
        self.bowling_probabilities = calculate_bowling_probabilities(self.all_innings_df)

        logging.debug("getting featured players")
        self.featured_player_df = self.data_selection.get_frequent_players_universe()

        logging.debug("PredictiveUtils setup complete")

        self.is_setup = True

    def populate_bowler_for_state(self, match_key: str, bowling_team: str,
                                  over: int, previous_bowler: str, playing_xi: list) -> str:
        """
        Calculate the bowler for the current state of the match using a multinomial distribution over the actual
        historical data
        """
        index = (bowling_team, over)
        if self.bowling_probabilities.isin(index):
            # Get the multinomial object corresponding to this state
            multinomial = self.bowling_probabilities.get_multinomial(index)

            # Look for a bowler using the multinomial distribution thrice
            for i in range(0, 3):
                # Get the predicted bowler
                selected_bowler_rv \
                    = multinomial.rvs(1, random_state=np.random.randint((over + 1) * match_key))[0]
                selected_bowler_id = np.where(selected_bowler_rv == 1)[0][0]
                bowler_key = self.bowling_probabilities.get_label(selected_bowler_id)
                # however, only set it if the predicted bowler is not the previous bowler and if they are in the
                # bowling playing xi
                if bowler_key != previous_bowler and bowler_key in playing_xi:
                    return bowler_key

        # Catch all if we couldn't find a bowler key yet - this assumes that the playing xi is usually sorted to
        # list the batters first & then the all-rounders and then the bowlers
        bowler_key = playing_xi[-1]
        if bowler_key == previous_bowler:
            bowler_key = playing_xi[-2]

        return bowler_key

    def calculate_probability_toss_winner_fields_first(self) -> pd.DataFrame:
        """
        Given a dataframe containing a list of matches, returns the probability of the toss winner choosing to bowl first,
        grouped by the venue & toss winning team. This function uses frequency counting & maps it to the probability.
        :param all_matches_df: The list of matches used to calculate the probability
        :return: pd.DataFrame which maps venue and team to a specific probability
        """
        frequencies_df = self.all_matches_df.groupby(['toss_winner', 'venue', 'toss_decision']).count()['key'].unstack()
        frequencies_df = frequencies_df.reset_index()
        frequencies_df = frequencies_df.fillna(0)

        frequencies_df['probability'] = frequencies_df['field'] / (frequencies_df['field'] + frequencies_df['bat'])
        frequencies_df.set_index(['toss_winner', 'venue'], inplace=True, verify_integrity=True)
        frequencies_df = frequencies_df.drop(['field', 'bat'], axis=1)

        return frequencies_df

    def compute_toss_results(self, scenario_and_match_df, number_of_scenarios, number_of_matches):
        """
        For the set of matches (key = scenario & match_key), calculate the toss winners & their actions, and update
        the scenario_and_match_df.
        """

        # 50% probability of either team winning the toss
        toss_won_by_team1_bernoulli = sps.bernoulli(p=0.5)
        scenario_and_match_df['toss_winner'] = scenario_and_match_df['team2']
        scenario_and_match_df['toss_loser'] = scenario_and_match_df['team1']
        mask = pd.Series(toss_won_by_team1_bernoulli.rvs(number_of_scenarios * number_of_matches,
                                                         random_state=np.random.randint(low=3)) == 1)

        scenario_and_match_df.loc[mask, 'toss_winner'] = scenario_and_match_df['team1']
        scenario_and_match_df.loc[mask, 'toss_loser'] = scenario_and_match_df['team2']

        toss_winner_action_probability_df = self.calculate_probability_toss_winner_fields_first()

        scenario_and_match_df['toss_decision'] = 'bat'

        # Calculate the toss action by looking at the distribution for the venue & toss winner
        for g, g_df in scenario_and_match_df.groupby(['toss_winner', 'venue']):
            if g in toss_winner_action_probability_df.index:
                probability_field_first = toss_winner_action_probability_df.loc[g]['probability']
            else:
                probability_field_first = toss_winner_action_probability_df['probability'].mean()
            field_first_bernoulli = sps.bernoulli(p=probability_field_first)
            mask = (field_first_bernoulli.rvs(len(g_df.index), random_state=np.random.randint(low=3)) == 1)

            g_df.loc[mask, 'toss_decision'] = 'field'
            scenario_and_match_df.loc[g_df.index, 'toss_decision'] = g_df['toss_decision']

        scenario_and_match_df['bowling_team'] = scenario_and_match_df['toss_winner']
        scenario_and_match_df['batting_team'] = scenario_and_match_df['toss_loser']
        mask = scenario_and_match_df['toss_decision'] == 'bat'
        scenario_and_match_df.loc[mask, 'bowling_team'] = scenario_and_match_df['toss_loser']
        scenario_and_match_df.loc[mask, 'batting_team'] = scenario_and_match_df['toss_winner']


def update_match_state(row, matches_dict):
    """
    Helper function to update the match state corresponding to the row
    """
    scenario = row.name[0]
    key = row.name[1]
    return matches_dict[(scenario, key)].update_state(row)
