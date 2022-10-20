import streamlit as st
import utils.page_utils as page_utils
import utils.config_utils as config_utils

def app():

    page_utils.setup_page(" Configure Sportiqo Rewards ")
    st.markdown('''
## Configure Sportiqo Rewards Formula Tab [v0.2]:

### Objective:
- Lets the user review/modify all the `rewards_formula_calculation_parameters`

### Defintions:

#### `rewards_formula_calculation_parameters`: 

Data structure representing static configuration for the rewards formula. Composed of:

- `batting_outcomes_parameters`: 
    - `base_reward`: A mapping from `batting_outcome_index` to `batting_outcome_reward`
    - `strike_rate_bonus_threshold`
    - `strike_rate_bonus_reward`
    - `strike_rate_penalty_threshold`
    - `strike_rate_penalty_reward`
- `bowling_outcomes_parameters`:
    - `base_reward`:
        - A mapping from `bowling_outcome_index` to `bowling_outcome_reward`
        - A mapping from `number_of_innings_wickets` to `innings_wickets_reward`
    - `economy_rate_bonus_threshold`
    - `economy_rate_bonus_reward`
    - `economy_rate_penalty_threshold`
    - `economy_rate_penalty_reward`
- `fielding_outcomes_parameters`:
    - `base_reward`:
        - A mapping from `fielding_outcome_index` to `bowling_outcome_reward`

    ''')

app()