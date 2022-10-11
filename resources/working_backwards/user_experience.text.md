5. **What does the customer experience look like?** 
    - Available Historical Data Tab:
        - Lets the user see all `available_t20_tournaments`
        - Lets the user set a `cut_off_tournament_for_training` 
        - Lets the user set a `cut_off_tournament_for_testing`
    - Review Perfect Simulation Tab:
        - Lets the user review `error_measures` for all `evaluation_metrics` assuming the simulator had full awareness 
        of what actually transpired in a match. The `evaluation_metrics_by_match_key` will have the following structure:
            - `batting_statistics_by_player_key`: A dataframe which
            - `bowling_statistics_by_player_key`
            - `fielding_statistics_by_player_key`
            - `sqortiqo_rewards_by_player_key`
    - Review Predictive Simulations Tab:
        - Lets the user review all the error metrics assuming the simulator only had awareness of the following
        variables in each match after the cutoff period:
            - `playing_xi_by_team_key`
            - `venue`
            - `venue_neutrality`
        - The Predictive Simulator will run match simulations as below:
            - Simulate the toss
            - Conditioned on the toss simulate the first_over_lineup:
                - First batting pair
                - First bowler
            - Conditioned on the first_over_lineup, simulate:
                - nth_ball_in_over_outcome where n = 1
            - Conditioned on the previous_ball_in_over_outcome, simulate:
                - next_ball_in_over_outcome
            - If the over is completed, Conditioned_on_the_previous_ball_in_over_outcome, simulate"
                - next_over_lineup
            - Repeat until first of 20 overs bowlers or 10 wickets fallen to produce first_innings_outcome
            - Conditioned on the first_innings_outcome, simulate second_innings_outcome, with an additional
            constrain to terminate if the target is reached.
    - Review Predictive Simulations Across Time Tab:
        - Pre-runs Predictive Simulation by iteratively setting the cut-off date one tournament ahead and presents a 
        graph where the x-axis represents the tournament and the y-axis represents the error measure on one of the 
        available metrics.