import streamlit as st
import utils.page_utils as page_utils
import utils.config_utils as config_utils

def app():

    page_utils.setup_page(" Review Inferential Models ")
    st.markdown('''
## Review Inferential Models Tab [v0.3]:

### Objective:

- Lets users evaluate the ability of inferential models to faithfully classify `bowling_outcomes_by_ball_and_innings` when `match_state_by_ball_and_innings` is known. 

- Lets users select one of the following inferential models and review `error_measures` on `inference_evaluation_metrics` specific to it:
    - `first_innings_bowling_outcomes_model`
    - `second_innings_bowling_outcomes_model`

- Lets users review these metrics for each model at the following granularities:
    - `by_player_and_innings_and_scenario`
    - `by_player_and_innnings`
    - `by_player_and_match`
    - `by_player_and_tournament_stage`
    - `by_player_and_tournament`

### Definitions:

#### `inferential_model`

- A model that uses data for all matches in the `training_window` to learn the
parameters for classifying `bowling_outcomes_by_ball_and_innings` when `match_state_by_ball_and_innings` is known.
- It is meant to produces desirable values of `inference_evaluation_metrics`. 
- v1.0 will include two `inferential_models`, one for the first inning and one for the second innings.
  
#### `inference_evaluation_metrics` 

A data structure used to evaluate the efficacy of an `inferential_model`. It is composed of:
- `precision_bowling_outcomes_by_ball_and_innings`
- `recall_bowling_outcomes_by_ball_and_innings`
- `f1_score_bowling_outcomes_by_ball_and_innings`
    
#### `match_state_by_ball_and_innings` 
A datastructure contains the following metadata about the state of the match before a specific ball was 
bowled:
- `batsman_id` (one-hot encoded)
- `bowler_id` (one-hot encoded)
- `batting_team_id` (one-hot encoded)
- `bowling_team_id` (one-hot encoded)
- `over_number` (one-hot encoded)
- `ball_number_in_over` (one-hot encoded)
- `venue_id` (one-hot encoded)
- `wickets_fallen`
- `current_total`
- `runs_to_target` [if second innings]

    ''')

app()