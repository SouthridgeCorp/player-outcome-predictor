# 5. What does the customer experience look like?

## Data Selection Tab:

### Objective:
- Lets the user see all `available_t20_tournaments`
- Lets the user select a list of `selected_tournaments` for model building and evaluation
- Lets the user set a `training_window` 
- Lets the user set a `testing_window`
- Summarises their selection and indicates the number of matches by `selected_tournament` for training and testing

## Configure Sportiqo Rewards Formula Tab:

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
        
#### `bowling_outcome_index`:

Represents mutually exclusive outcomes for a bowler, composed of:
- [0, 1-b, 1-oe, 1-nb, 1-w,  2-b…. 6-b, 6-oe, 6-nb, 6-w, W-b, W-nb]
- 0 : dot_ball
- 1-b : 1 run, attributable to batsman
- 1-nb: 1 run, attributable to no ball
- 1-w: 1 run, attributable to wide
- 1-oe: 1 run, attributable to other extras
- ... for upto 6 runs
- W-b: wicket, attributable to bowler along
- W-bc: wicket, catch, attributable to bowler and fielder
- W-bs: wicket, stumping, attributable to bowler and fielder
- W-dro: wicket, direct run-out
- W-idro: wicket, indirect run-out
- W-others: other forms of dismissal not attributable to bowler

#### `batting_outcome_index`:

Represents mutually exclusive outcomes for a batsman, composed of
- [0, 1-b, 2-b, 3-b, 4-b, 5-b, 6-b, W]
- 0 : dot_ball, and other bowling_outcomes not attributable to batsman, excluding wickets
- 1-b: same as 1-b bowling_outcome
- ... for upto 6 runs
- W: union of W-b, W-bc, W-bs, W-dro, W-idro, W-others from bowling_outcome

#### `fielding_outcome_index`

Represents mutually exclusive outcomes for a fielder, composed of
- [w-c,w-s,w-dro,w-idro]
- w-c: catch,
- w-s: stumping
- w-dro: direct run out
- w-idro: indirect run out


## Review Perfect Simulation Tab:

### Objective:
- Lets the user review all the `error_measures` and `simulation_evaluation_metrics` for each innings, match, tournament_stage 
and tournament in the `testing_window`, as projected by the `perfect_simulation_model`
- The user will be able to view aggregations on both `error_measures` and `evaluation_metrics` at the following
granularities:
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

## Review Inferential Models Tab:

### Objective:
- Lets users evaluate the ability inferential models which will 
- Lets the user select one of the following inferential models and review `error_measures` on `inference_evaluation_metrics` specific to it:
    - `first_innings_bowling_outcomes_model`
    - `second_innings_bowling_outcomes_model`
- Lets the user review these metrics for each model at the following granularities:
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
    
## Review Predictive Simulations Tab:

### Objective:
- Lets the user review all the `error_measures` and `simulation_evaluation_metrics` for each innings, match, tournament_stage 
and tournament in the `testing_window`, as projected by the `predictive_simulation_model`
- The user will be able to view aggregations on both `error_measures` and `simulation_evaluation_metrics` at the following
granularities:
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

## Simulate Tournament Tab:

### Objective:
- Lets the user configure an `upcoming_tournament` and use the `predictive_simulation_model` to produce a 
`reliable_simulation` for the tournament.
- Lets the user review the `rewards_by_player_and_tournament` for the `focus_players` and perform
basic sensitivity analysis on the `rewards_formula_calculation_parameters`
- To be used for discussion on design of the `reward_fairness_metric`. Once designed, it will also be shown here. 

### Definitions:
- An `upcoming_tournament` is composed of:
    - `playing_teams`
    - `playing_xi_by_team_key`
    - `tournament_format`: Current version will only implement round robin league with eliminator based playoffs.
    - `focus_players`: 5 players per team for whom player counters are to be auctioned.


