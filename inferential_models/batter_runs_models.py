import numpy as np
import pandas as pd
import pymc as pm
from sklearn.preprocessing import OneHotEncoder
import aesara.tensor as at
from simulators.perfect_simulator import PerfectSimulator


class BatterRunsModel:
    """Class to instantiate a ball level outcomes predictor for batter runs"""

    def __init__(self,
                 perfect_simulator: PerfectSimulator,
                 selected_tournament: str,
                 selected_season: str):
        perfect_simulator.data_selection.
        self.all_bowling_outcomes_df = perfect_simulator.
