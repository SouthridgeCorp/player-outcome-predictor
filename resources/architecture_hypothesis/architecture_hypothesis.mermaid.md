graph LR
    historical_data --> data_selection
    
    rewards_configuration --> perfect_simulator
    data_selection --> perfect_simulator
    
    data_selection --> inferential_models
    
    inferential_models --> predictive_simulator
    data_selection --> predictive_simulator

    predictive_simulator --> tournament_simulation
    upcoming_tournament --> tournament_simulation