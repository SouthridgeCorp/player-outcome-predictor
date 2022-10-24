graph LR

    historical_ball_by_ball_outcomes --> match_state_by_ball_and_innings

    filter_train --> bowling_outcomes_model_by_innings
    match_state_by_ball_and_innings --> bowling_outcomes_model_by_innings
    bowling_outcomes_by_ball_and_innings --> bowling_outcomes_model_by_innings

    filter_test --> projected_bowling_outcomes_by_ball_and_innings
    match_state_by_ball_and_innings --> projected_bowling_outcomes_by_ball_and_innings
    bowling_outcomes_model_by_innings --> projected_bowling_outcomes_by_ball_and_innings
    projected_bowling_outcomes_by_ball_and_innings --> match_state_by_ball_and_innings

    projected_bowling_outcomes_by_ball_and_innings --> projected_evaluation_metrics_by_player_and_tournament

    filter_test --> test_evaluation_metrics_by_player_and_tournament
    match_state_by_ball_and_innings --> test_evaluation_metrics_by_player_and_tournament
    bowling_outcomes_by_ball_and_innings --> test_evaluation_metrics_by_player_and_tournament

    test_evaluation_metrics_by_player_and_tournament --> test_error_measures_by_player_and_tournament
    projected_evaluation_metrics_by_player_and_tournament --> test_error_measures_by_player_and_tournament

    historical_ball_by_ball_outcomes --> bowling_outcomes_by_ball_and_innings

    bowling_outcomes_by_ball_and_innings --> batting_outcomes_by_ball_and_innings
    bowling_outcomes_by_ball_and_innings --> fielding_outcomes_by_ball_and_innings

    bowling_outcomes_by_ball_and_innings --> precision_bowling_outcomes_by_ball_and_innings
    bowling_outcomes_by_ball_and_innings --> recall_bowling_outcomes_by_ball_and_innings
    bowling_outcomes_by_ball_and_innings --> f1_score_bowling_outcomes_by_ball_and_innings


    batting_outcomes_by_ball_and_innings --> batting_base_rewards_by_ball_and_innings
    batting_base_reward --> batting_base_rewards_by_ball_and_innings

    bowling_outcomes_by_ball_and_innings --> bowling_base_rewards_by_ball_and_innings
    bowling_base_reward --> bowling_base_rewards_by_ball_and_innings
    wickets_taken_by_player_and_innings --> bowling_base_rewards_by_ball_and_innings

    fielding_outcomes_by_ball_and_innings --> fielding_base_rewards_by_ball_and_innings
    fielding_base_reward --> fielding_base_rewards_by_ball_and_innings

    batting_outcomes_by_ball_and_innings --> batting_strike_rate_by_player_and_innings
    batting_outcomes_by_ball_and_innings --> batting_strike_rate_by_team_and_innings
    
    bowling_outcomes_by_ball_and_innings --> bowling_economy_rate_by_player_and_innings
    bowling_outcomes_by_ball_and_innings --> bowling_economy_rate_by_team_and_innings
    bowling_outcomes_by_ball_and_innings --> wickets_taken_by_player_and_innings

    batting_strike_rate_by_player_and_innings --> batting_penalty_by_player_and_innings
    batting_strike_rate_by_team_and_innings --> batting_penalty_by_player_and_innings
    strike_rate_penalty_threshold --> batting_penalty_by_player_and_innings
    strike_rate_penalty_reward --> batting_penalty_by_player_and_innings

    batting_strike_rate_by_player_and_innings --> batting_bonus_by_player_and_innings
    batting_strike_rate_by_team_and_innings --> batting_bonus_by_player_and_innings
    strike_rate_bonus_threshold --> batting_bonus_by_player_and_innings
    strike_rate_bonus_reward --> batting_bonus_by_player_and_innings
    
    bowling_economy_rate_by_player_and_innings --> bowling_penalty_by_player_and_innings
    bowling_economy_rate_by_team_and_innings --> bowling_penalty_by_player_and_innings
    economy_rate_penalty_threshold --> bowling_penalty_by_player_and_innings
    economy_rate_penalty_reward --> bowling_penalty_by_player_and_innings

    bowling_economy_rate_by_player_and_innings --> bowling_bonus_by_player_and_innings
    bowling_economy_rate_by_team_and_innings --> bowling_bonus_by_player_and_innings
    economy_rate_bonus_threshold --> bowling_bonus_by_player_and_innings
    economy_rate_bonus_reward --> bowling_bonus_by_player_and_innings

    batting_base_rewards_by_ball_and_innings --> batting_rewards_by_player_and_innings
    batting_penalty_by_player_and_innings --> batting_rewards_by_player_and_innings
    batting_bonus_by_player_and_innings --> batting_rewards_by_player_and_innings
    
    bowling_base_rewards_by_ball_and_innings --> bowling_rewards_by_player_and_innings
    bowling_penalty_by_player_and_innings --> bowling_rewards_by_player_and_innings
    bowling_bonus_by_player_and_innings --> bowling_rewards_by_player_and_innings

    fielding_base_rewards_by_ball_and_innings --> fielding_rewards_by_player_and_innings

    batting_rewards_by_player_and_innings --> rewards_by_player_and_innings
    bowling_rewards_by_player_and_innings --> rewards_by_player_and_innings
    fielding_rewards_by_player_and_innings --> rewards_by_player_and_innings

    rewards_by_player_and_innings --> rewards_by_player_and_match
    rewards_by_player_and_match --> rewards_by_player_and_tournament_stage
    rewards_by_player_and_tournament_stage --> rewards_by_player_and_tournament

    batting_rewards_by_player_and_innings --> batting_rewards_by_player_and_match
    batting_rewards_by_player_and_match --> batting_rewards_by_player_and_tournament_stage
    batting_rewards_by_player_and_tournament_stage --> batting_rewards_by_player_and_tournament

    bowling_rewards_by_player_and_innings --> bowling_rewards_by_player_and_match
    bowling_rewards_by_player_and_match --> bowling_rewards_by_player_and_tournament_stage
    bowling_rewards_by_player_and_tournament_stage --> bowling_rewards_by_player_and_tournament

    fielding_rewards_by_player_and_innings --> fielding_rewards_by_player_and_match
    fielding_rewards_by_player_and_match --> fielding_rewards_by_player_and_tournament_stage
    fielding_rewards_by_player_and_tournament_stage --> fielding_rewards_by_player_and_tournament

    subgraph outcomes_by_ball_and_innings
        batting_outcomes_by_ball_and_innings

        bowling_outcomes_by_ball_and_innings

        fielding_outcomes_by_ball_and_innings
    end

    subgraph outcomes_by_player_and_innings
        batting_strike_rate_by_player_and_innings

        bowling_economy_rate_by_player_and_innings
        wickets_taken_by_player_and_innings
    end

    subgraph outcomes_by_team_and_innings
        batting_strike_rate_by_team_and_innings

        bowling_economy_rate_by_team_and_innings
        
    end

    subgraph rewards
        batting_base_rewards_by_ball_and_innings
        batting_bonus_by_player_and_innings
        batting_penalty_by_player_and_innings

        bowling_base_rewards_by_ball_and_innings
        bowling_bonus_by_player_and_innings
        bowling_penalty_by_player_and_innings

        fielding_base_rewards_by_ball_and_innings
    end

    subgraph inference_evaluation_metrics
        precision_bowling_outcomes_by_ball_and_innings
        recall_bowling_outcomes_by_ball_and_innings
        f1_score_bowling_outcomes_by_ball_and_innings
    end

    subgraph simulation_evaluation_metrics
        rewards_by_player_and_innings
        batting_rewards_by_player_and_innings
        bowling_rewards_by_player_and_innings
        fielding_rewards_by_player_and_innings

        rewards_by_player_and_match
        batting_rewards_by_player_and_match
        bowling_rewards_by_player_and_match
        fielding_rewards_by_player_and_match

        rewards_by_player_and_tournament
        batting_rewards_by_player_and_tournament
        bowling_rewards_by_player_and_tournament
        fielding_rewards_by_player_and_tournament

        rewards_by_player_and_tournament_stage
        batting_rewards_by_player_and_tournament_stage
        bowling_rewards_by_player_and_tournament_stage
        fielding_rewards_by_player_and_tournament_stage
    end

    subgraph rewards_formula_calculation_parameters
        batting_base_reward

        bowling_base_reward

        strike_rate_bonus_threshold
        strike_rate_bonus_reward
        strike_rate_penalty_threshold
        strike_rate_penalty_reward

        economy_rate_bonus_threshold
        economy_rate_bonus_reward
        economy_rate_penalty_threshold
        economy_rate_penalty_reward

        fielding_base_reward
    end

    subgraph raw_data
        historical_ball_by_ball_outcomes
    end

    subgraph dynamic_inputs
        filter_train
        filter_test
    end

    subgraph inferential_model
        bowling_outcomes_model_by_innings
    end

    subgraph predictive_simulation
        projected_bowling_outcomes_by_ball_and_innings
        match_state_by_ball_and_innings
        projected_bowling_outcomes_by_ball_and_innings
        projected_evaluation_metrics_by_player_and_tournament
    end

    subgraph evaluation
        test_evaluation_metrics_by_player_and_tournament
        test_error_measures_by_player_and_tournament
    end