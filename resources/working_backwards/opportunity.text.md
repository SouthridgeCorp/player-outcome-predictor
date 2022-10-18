2. **What is the customer problem or opportunity?** 
    - A reliable simulation of a match takes the following static variables as input:
        - `playing_xi_by_team_key`: List of `players` including their `player_keys` who played the match
        - `venue_key`: Where was the match played
        - `actual_ball_by_ball_outcomes_by_match_key`: What were the actual outcomes on each ball of the match
        - `historical_first_innings_ball_by_ball_outcomes_by_batsman_bowler_pair_key`: A dataframe consisting of the historical
        head to head outcomes (where available) for each pair of [batsman, bowler] between the 2 playing teams in first innings
        - `historical_second_innings_ball_by_ball_outcomes_by_batsman_bowler_pair_key`: A dataframe consisting of the historical
        head to head outcomes (where available) for each pair of [batsman, bowler] between the 2 playing teams in second innings
    - A reliable simulation of a match takes the following dynamic variables as input:
        - `number_of_scenarios`: The number of scenarios to simulate for the match
    - A reliable simulation of a match produces the following `evaluation_metrics`:
        - `batting_stats_by_player_key`:
            - `dot_balls_by_batting_player_key`
            - `singles_by_batting_player_key`
            - `doubles_by_batting_player_key`
            - etc
            - `dismissal_by_batting_player_key`
            - `strike_rate_by_batting_player_key`
        - `bowling_stats_by_player_key`
        - `fielding_stats_by_player_key`
        - `sportiqo_rewards_by_player_key`
        - Each of these metrics will have an `actual` version derived from the true outcome and will have a 
        `simulated_per_scenario` version, which can be aggregated into `projection_across_scenarios` by taking
        an expectation over the scenarios.
        - The simulation will produce a report of the following error measures between `actual`, 
        `simulated_per_scenario` and `projection_across_scenarios` for each of the above metrics
            - `mean_absolute_error`
            - `mean_absolute_percentage_error`
        - Further these metrics can be re-aggregated at the following levels:
            - `match_level`: Error for all players in the match
            - `tournament_level`: Error for all matches in a tournament
            - `match_level_by_player_key`: Error for a player_key aggregated across all the matches they play in
            the `evaluation_window`
            - `tournament_level_by_player_key`: Error for a player_key aggregated across all the tournaments they
            played in the `evaluation_window`
    - The Predictive Simulator will run match simulations for a selected `num_scenarios` as below:
        - Simulate the toss
        - Conditioned on the toss, simulate the `innings_layout`, i.e which teams bat first/second,
        - Conditioned on the `innings_layout` simulate the `first_over_lineup`:
            - First batting pair
            - First bowler
        - Conditioned on the `first_over_lineup`, simulate:
            - `nth_ball_in_over_outcome` by using the appropriate `inferential_models` 
        - If the over is completed, conditioned on the `nth_ball_in_over_outcome`, simulate
            - next_over_lineup
        - Repeat until first of 20 overs bowlers or 10 wickets fallen to produce `first_innings_outcome`
        - Conditioned on the `first_innings_outcome`, simulate second_innings_outcome, with an additional
        constrain to terminate if the target is reached.
    - The `inferential models` will be used to estimate parameters for simulating ball by ball outcomes.
        - The models will assume availability of the following information for inference:
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
        - In addition, the models will assume availability of the following information for training and testing:
            - `batsman_outcome_index` [0, 1-b, 2-b, 3-b, 4-b, 5-b, 6-b, W]
            - `bowler_outcome_index` [0, 1-b, 1-oe, 1-nb, 1-w,  2-b…. 6-b, 6-oe, 6-nb, 6-w, W-b, W-nb]
            - `fielder_outcome_index` [c,s,dro,idro]
        - By using the historical data available in the above format, 6 inferential models will be learnt using bayesian
        multinomial logistic regression on the appropriate outcome vector:
            - `first_innings_batting_outcomes_model`
            - `first_innings_bowling_outcomes_model`
            - `first_innings_fielding_outcomes_model`
            - `second_innings_batting_outcomes_model`
            - `second_innings_bowling_outcomes_model`
            - `second_innings_fielding_outcomes_model`
