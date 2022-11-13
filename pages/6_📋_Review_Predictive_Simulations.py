import streamlit as st
import utils.page_utils as page_utils
from utils.app_utils import data_selection_instance, rewards_instance
from simulators.predictive_simulator import PredictiveSimulator
from simulators.perfect_simulator import PerfectSimulator, Granularity
def app():
    page_utils.setup_page(" Review Predictive Simulation ")

    data_selection = data_selection_instance()
    tournaments = data_selection.get_helper().tournaments
    rewards = rewards_instance()

    granularity_list = ['None', Granularity.TOURNAMENT, Granularity.STAGE, Granularity.MATCH, Granularity.INNING]
    granularity = st.selectbox("Please select the granularity for reviewing Simulator stats", granularity_list)

    if granularity == 'None':
        st.write("Please select a valid Granularity")
    else:

        number_of_scenarios = 3
        predictive_simulator = PredictiveSimulator(data_selection, rewards, number_of_scenarios)
        perfect_simulator = PerfectSimulator(data_selection, rewards)
        with st.spinner("Generating Scenarios"):
            predictive_simulator.generate_scenario()

        scenario = st.selectbox(
            'Select a scenario:', range(0, number_of_scenarios))

        with st.spinner('Calculating Error Measures'):
            comparison_df = predictive_simulator.perfect_simulators[scenario].\
                get_simulation_evaluation_metrics_by_granularity(True, granularity)
            errors_df = perfect_simulator.get_error_measures(True, comparison_df, granularity)

        st.write(errors_df)






    st.markdown('''
## Review Predictive Simulations Tab [v0.4]:

### Objective:
- Lets the user review all the `error_measures` and `simulation_evaluation_metrics` for each innings, match, tournament_stage 
and tournament in the `testing_window`, as projected by the `predictive_simulation_model`
- The user will be able to view aggregations on both `error_measures` and `simulation_evaluation_metrics` at the following granularities:
    - `by_player_and_innnings`
    - `by_player_and_match`
    - `by_player_and_tournament_stage`
    - `by_player_and_tournament`
- Lets the user view the projected `top_k` best performing players in each team as measured by `evaluation_metrics.rewards_by_player`:
    - `top_k_players_by_team_and_tournament`
    - `top_k_batsmen_by_team_and_tournament`
    - `top_k_bowlers_by_team_and_tournament`

### Definitions:

#### `predictive_simulation_model`

A model that generates a set of `credible_scenarios` by using the `inferential_models` to simulate entire tournaments
by building them from ball by ball outcomes. Each `credible_scenario` will be associated with a set of `simulation_evaluation_metrics`.
    ''')


app()
