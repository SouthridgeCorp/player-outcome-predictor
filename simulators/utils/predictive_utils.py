import scipy.stats as sps
import pandas as pd
import numpy as np
from data_selection.data_selection import DataSelection

class PredictiveUtils:
    def __init__(self, data_selection: DataSelection):
        self.data_selection = data_selection


    def calculate_probability_toss_winner_fields_first(self) -> pd.DataFrame:
        """
        Given a dataframe containing a list of matches, returns the probability of the toss winner choosing to bowl first,
        grouped by the venue & toss winning team. This function uses frequency counting & maps it to the probability.
        :param all_matches_df: The list of matches used to calculate the probability
        :return: pd.DataFrame which maps venue and team to a specific probability
        """
        all_matches_df = self.data_selection.get_all_matches()
        frequencies_df = all_matches_df.groupby(['toss_winner', 'venue', 'toss_decision']).count()['key'].unstack()
        frequencies_df = frequencies_df.reset_index()
        frequencies_df = frequencies_df.fillna(0)

        frequencies_df['probability'] = frequencies_df['field'] / (frequencies_df['field'] + frequencies_df['bat'])
        frequencies_df.set_index(['toss_winner', 'venue'], inplace=True, verify_integrity=True)
        frequencies_df = frequencies_df.drop(['field', 'bat'], axis=1)

        return frequencies_df


    def compute_toss_results(self, scenario_and_match_df, number_of_scenarios, number_of_matches):
        toss_won_by_team1_bernoulli = sps.bernoulli(p=0.5)

        mask = pd.Series(toss_won_by_team1_bernoulli.rvs(number_of_scenarios * number_of_matches,
                                                           random_state=np.random.randint(low=3)) == 1)

        scenario_and_match_df.loc[mask, 'toss_winner'] = scenario_and_match_df['team1']

        toss_winner_action_probability_df = self.calculate_probability_toss_winner_fields_first()

        for g, g_df in scenario_and_match_df.groupby(['toss_winner', 'venue']):
            if g in toss_winner_action_probability_df.index:
                probability_field_first = toss_winner_action_probability_df.loc[g]['probability']
            else:
                probability_field_first = toss_winner_action_probability_df['probability'].mean()
            field_first_bernoulli = sps.bernoulli(p=probability_field_first)
            mask = (field_first_bernoulli.rvs(len(g_df.index), random_state=np.random.randint(low=3)) == 1)

            g_df.loc[mask, 'toss_decision'] = 'field'
            scenario_and_match_df.loc[g_df.index, 'toss_decision'] = g_df['toss_decision']


"""
class PredictiveUtils:
    def __init__(self, number_of_scenarios):
        self.random_number_list = list(np.random.randint(low=3, size=number_of_scenarios))
        self.toss_winner_fields_first_probabilities_df = None

    def setup_with_matches(self, matches_df):
        self.toss_winner_fields_first_probabilities_df = calculate_probability_toss_winner_fields_first(matches_df)

        self.toss_winner_fields_first_probabilities_df['bernoulli_dist'] = \
            self.toss_winner_fields_first_probabilities_df.apply(
                lambda x: sps.bernoulli(p=x['normalised_fielding']), axis=1)

    def compute_toss_winner_action(self, row, scenario_number):
        team = row['toss_winner']
        venue = row['venue']
        probability = row['normalised_fielding']

        probability_bd = sps.bernoulli(p=probability)
        probability_value = probability_bd.rvs(1, random_state=self.random_number_list[scenario_number - 1])[0]

        return "field" if probability_value == 1 else "bat"

    def predict_toss_winner(self, scenario_number: int, matches_df: pd.DataFrame):
        toss_won_by_team1_probability = sps.bernoulli(p=0.5)
        toss_won_by_team1_outcome_by_matches = toss_won_by_team1_probability.rvs(
            len(matches_df.index), random_state=self.random_number_list[scenario_number - 1])
        matches_df['predicted_team_1_won_toss'] = toss_won_by_team1_outcome_by_matches

        mask = matches_df['predicted_team_1_won_toss'] == 1
        matches_df.loc[mask, 'predicted_toss_winner'] = matches_df['team1']
        matches_df.loc[~mask, 'predicted_toss_winner'] = matches_df['team2']

    def predict_toss_winner_action(self, matches_df, scenario_number):
        matches_df = pd.merge(matches_df, self.toss_winner_fields_first_probabilities_df,
                              left_on=["predicted_toss_winner", "venue"], right_index=True)

        matches_df['predicted_toss_winner_fields'] \
            = matches_df['bernoulli_dist'].values.rvs(1, random_state=self.random_number_list[scenario_number - 1])[0]
        matches_df['predicted_toss_winner_fields'] = matches_df.apply(
            lambda x: self.compute_toss_winner_action(x, scenario_number), axis=1)
        print("hello")


"""
