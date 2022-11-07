import scipy.stats as sps
from data_selection.data_selection import DataSelection

class Predictive_Simulator:

    def __init__(self, data_selection:DataSelection, number_of_sequences):
        self.data_selection = data_selection
        self.number_of_sequences = number_of_sequences


    def generate_sequence(self):
        pass

    def predict_selected_matches(self, sequence_number: int):
        matches_df = self.data_selection.get_selected_matches()
        number_of_matches = len(matches_df.index)

        static_columns = []
        columns_to_predict = []
