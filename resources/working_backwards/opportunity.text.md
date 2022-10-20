2. **What is the customer problem or opportunity?** 
    - Inferential models of ball by ball outcomes by themselves do not produce simulations and credible intervals around 
    innings, match, tournament_stage and tournament level performance metrics at a player level. 
    - This application addresses this issue by adopting a hybrid approach:
        - An `inferential_model` is built to classify `bowling_outcomes_by_ball_and_innings` given available information
        on `match_state_by_ball_and_innings`, for each innings of the match, by inferring the parameters
        - A `predictive_simulation_model` uses the `inferential_model` to produce a `predictive_simulation` for 
        modeling entire tournaments by building up a range of `credible_scenarios` which incorporate the following
        sources of randomness:
            - `toss_outcome`
            - `toss_decision`
            - `bowling_outcomes_by_ball_and_innings`
            - `match_state_by_ball_and_innings`
        - The `predictive_simulation_model` encodes the impact of these sources of randomness on the following downstream
        variables:
            - `batting_outcomes_by_ball_and_innings`
            - `fielding_outcomes_by_ball_and_innings`
            - `match_state_by_ball_and_innings`
        - The `predictive_simulation_model` makes the following simplifying assumptions:
            - The starting batting pair for each team is known for the length of the tournament.
            - The choice of the new batsman on a dismissal is made by sampling from the frequency distribution of batting
            positions of all remaining batsmen
            - The choice of bowler at for a new over is made by sampling from the frequency distribution of bowlers
            having bowled a specific over number
        - This ultimately facilitates generation of `credible_scenarios` for each ball, over, innings, match, tournament
        stage and tournament.
        - By analysing measures of centrality and dispersion of `simulation_evaluation_metrics` across `credible_scenarios`
        the application will enable decisions on setting the base auction price for players in a tournament


