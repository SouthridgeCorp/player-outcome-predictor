5. **What does the customer experience look like?** 
    - Available Historical Data Tab:
        - Lets the user see all `available_t20_tournaments`
        - Lets the user set a `cut_off_tournament_for_training` 
        - Lets the user set a `cut_off_tournament_for_testing`
    - Configure Sportiqo Rewards Formula Tab:
        - Lets the user review/modify all the `rewards_formula_calculation_parameters`:
            - `batting_outcomes_parameters`: 
                - `base_reward` :A mapping from `batting_outcome_index` to `batting_outcome_reward`
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
    - Review Perfect Simulation Tab:
        - Lets the user review `error_measures` for all `evaluation_metrics` assuming the simulator had full awareness 
        of what actually transpired in a match in the `cut_off_tournament_for_testing`. The `evaluation_metrics_by_match_key` will have the following structure:
            - `batting_statistics_by_player_key`
            - `bowling_statistics_by_player_key`
            - `fielding_statistics_by_player_key`
            - `sqortiqo_rewards_by_player_key`
        - Shows summary statistics for a few key data points:
            - `top_5_bowlers_by_team`: A dataframe showing the top 5 bowlers for each team, as ranked by `sportiqo_rewards_by_player_key`
            - `top_5_batsmen_by_team`: A dataframe showing the top 5 batsment for each team, as ranked by `sportiqo_rewards_by_player_key`
    - Review Inferential Models Tab:
        - Lets the user review select one of the following inferential models and review `error_measures` on `evaluation_metrics` specific to it:
            - `first_innings_batting_outcomes_model`
            - `first_innings_bowling_outcomes_model`
            - `first_innings_fielding_outcomes_model`
            - `second_innings_batting_outcomes_model`
            - `second_innings_bowling_outcomes_model`
            - `second_innings_fielding_outcomes_model`
    - Review Predictive Simulations Tab:
        - Lets the user review all the error metrics assuming the simulator only had awareness of the following
        variables in each match after the cutoff period:
            - `playing_xi_by_team_key`
            - `venue`
    - Review Predictive Simulations Across Time Tab:
        - Pre-runs Predictive Simulation by iteratively setting the cut-off date one tournament ahead and presents a 
        graph where the x-axis represents the tournament and the y-axis represents the `error_measures` on one of the 
        available `evaluation_metrics`.
    - Simulate Tournament Tab:
        - Lets the user configure an `upcoming_tournament` and use the application to produce a `reliable_simulation` 
        for the tournament. An `upcoming_tournament` is defined as:
            - `playing_teams`
            - `playing_xi_by_team_key`
            - `tournament_format`: Current version will only implement round robin league with eliminator based playoffs.
            - `focus_players`: 5 players per team for whom player counters are to be auctioned.
        - Lets the user review the `projected_sportiqo_rewards_by_player_key` for the `focus_players` and perform
        basic sensitivity analysis on the `rewards_formula_calculation_parameters`
        - To be used for discussion on design of the "fairness" metric. Once designed, it will also be shown here.

