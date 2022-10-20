import streamlit as st
import utils.page_utils as page_utils
import utils.config_utils as config_utils

def app():

    page_utils.setup_page(" Review Predictive Simulation ")
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