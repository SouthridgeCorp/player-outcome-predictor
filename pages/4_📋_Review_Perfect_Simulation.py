import streamlit as st
import utils.page_utils as page_utils
import utils.config_utils as config_utils

def app():

    page_utils.setup_page(" Configure Sportiqo Rewards ")
    st.markdown('''
## Review Perfect Simulation Tab [v0.2]:

### Objective:
- Lets the user review all the `error_measures` and `simulation_evaluation_metrics` for each innings, match, tournament_stage 
and tournament in the `testing_window`, as projected by the `perfect_simulation_model`

- The user will be able to view aggregations on both `error_measures` and `evaluation_metrics` at the following granularities:
    - `by_player_and_innnings`
    - `by_player_and_match`
    - `by_player_and_tournament_stage`
    - `by_player_and_tournament`

- Lets the user view the `top_k` best performing players in each team as measured by `evaluation_metrics.rewards_by_player`:
    - `top_k_players_by_team_and_tournament`
    - `top_k_batsmen_by_team_and_tournament`
    - `top_k_bowlers_by_team_and_tournament`

### Definitions:

#### `perfect_simulation_model`:

A retrospective simulationmodel that assumes full knowledge of everything that transpired in each ball, innings, match,
tournament_stage and tournament to produce `simulation_evaluation_metrics`

#### `simulation_evaluation_metrics`

A data structure that is used to compare the outputs of two or more simiulations. It is composed of:
- `rewards_by_player_and_innings`
- `batting_rewards_by_player_and_innings`
- `bowling_rewards_by_player_and_innings`
- `fielding_rewards_by_player_and_innings`

#### `error_measures`

Consists of the following metrics calculated for each `simulation_evaluation_metric` in the course of comparison:
- `mean_absolute_error`
- `mean_absolute_percentage_error`

    ''')

app()