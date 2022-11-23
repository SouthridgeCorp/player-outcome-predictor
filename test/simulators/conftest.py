import pytest

from inferential_models.batter_runs_models import BatterRunsModel
from rewards_configuration.rewards_configuration import RewardsConfiguration
from data_selection.data_selection import DataSelection
from historical_data.singleton import Helper
from simulators.perfect_simulator import PerfectSimulator
from simulators.predictive_simulator import PredictiveSimulator
from simulators.tournament_simulator import TournamentSimulator


@pytest.fixture
def perfect_simulator(setup_and_teardown):
    test_case, config_instance = setup_and_teardown
    rewards_config = RewardsConfiguration(config_instance)

    helper = Helper(config_instance)

    data_selection = DataSelection(helper)

    simulator = PerfectSimulator(data_selection, rewards_config)
    yield simulator


@pytest.fixture
def predictive_simulator(setup_and_teardown):
    test_case, config_instance = setup_and_teardown
    rewards_config = RewardsConfiguration(config_instance)

    helper = Helper(config_instance)

    data_selection = DataSelection(helper)

    number_of_scenarios = config_instance.get_predictive_simulator_info()

    perf_simulator = PerfectSimulator(data_selection, rewards_config)

    batter_runs_model = BatterRunsModel(perf_simulator)

    simulator = PredictiveSimulator(data_selection,
                                    rewards_config,
                                    batter_runs_model,
                                    number_of_scenarios)
    yield simulator


@pytest.fixture
def tournament_simulator(setup_and_teardown):
    test_case, config_instance = setup_and_teardown
    rewards_config = RewardsConfiguration(config_instance)

    helper = Helper(config_instance)

    data_selection = DataSelection(helper)

    perf_simulator = PerfectSimulator(data_selection, rewards_config)

    batter_runs_model = BatterRunsModel(perf_simulator)

    simulator = TournamentSimulator(data_selection,
                                    rewards_config,
                                    batter_runs_model,
                                    config_instance)
    yield simulator
