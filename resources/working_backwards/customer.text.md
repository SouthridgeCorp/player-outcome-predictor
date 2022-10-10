1. **Who is the customer**?
   - The management team of Sportiqo will use this application to take the following decision:
        - Evaluate whether the application produces reliable simulations of historical IPL T20 matches included in
        `data/historical/ipl_matches_metadata.csv` and `data/historical/ipl_matches_ball_by_ball.csv`
            - A reliable simulation of a match takes the following static variables as input:
                - `playing_xi_by_team_key`: List of `players` including their `player_keys` who played the match
                - `venue_key`: Where was the match played
                - `venue_neutrality`: Was the match played at a neutral venue for both teams
                - `actual_ball_by_ball_outcomes_by_match_key`: What were the actual outcomes on each ball of the match
                - `historical_first_innings_ball_by_ball_outcomes_by_batsman_bowler_pair_key`: A dataframe consisting of the historical
                head to head outcomes (where available) for each pair of [batsman, bowler] between the 2 playing teams in first innings
                - `historical_second_innings_ball_by_ball_outcomes_by_batsman_bowler_pair_key`: A dataframe consisting of the historical
                head to head outcomes (where available) for each pair of [batsman, bowler] between the 2 playing teams in second innings
            - A reliable simulation of a match takes the following dynamic variables as input:
                - `number_of_scenarios`: The number of scenarios to simulate for the match
            - A reliable simulation of a match produce the following output metrics:
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
                `simulated_per_scenario` and `projection_across_scenarios` for each of the above metrics"
                    - `mean_absolute_error`
                    - `mean_absolute_percentage_error`
                - Further these metrics can be re-aggregated at the following levels:
                    - `match_level`: Error for all players in the match
                    - `tournament_level`: Error for all matches in a tournament
                    - `match_level_by_player_key`: Error for a player_key aggregated across all the matches they play in
                    the `evaluation_window`
                    - `tournament_level_by_player_key`: Error for a player_key
