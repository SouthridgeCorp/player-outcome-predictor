graph LR
    historical_data --> data_selection_ui
    training_window --> data_selection_ui
    testing_window --> data_selection_ui
    
    data_selection_ui --> data_selection
    data_selection --> data_selection_ui

    rewards_configuration_ui --> rewards_configuration    
    rewards_configuration --> rewards_configuration_ui    
    
    rewards_configuration --> perfect_simulation_ui
    data_selection --> perfect_simulation_ui
    
    perfect_simulation_ui --> perfect_simulator
    perfect_simulator --> perfect_simulation_ui    

    perfect_simulator --> inferential_models_ui
    
    inferential_models_ui --> inferential_models
    inferential_models --> inferential_models_ui
    
    inferential_models --> predictive_simulation_ui
    perfect_simulator --> predictive_simulation_ui
    
    predictive_simulation_ui --> predictive_simulator
    predictive_simulator --> predictive_simulation_ui

    predictive_simulator --> tournament_simulation_ui
    upcoming_tournament --> tournament_simulation_ui
    
    tournament_simulation_ui --> tournament_simulator

    subgraph v0.1
        data_selection_ui
        historical_data
        data_selection
    end

    subgraph v0.2
        rewards_configuration_ui
        perfect_simulation_ui
        rewards_configuration
        perfect_simulator
    end

    subgraph v0.3
        inferential_models_ui
        inferential_models
    end

    subgraph v0.4
        predictive_simulation_ui
        predictive_simulator
    end

    subgraph v0.5
        tournament_simulation_ui
        tournament_simulator
    end

    subgraph dynamic_inputs
        training_window
        testing_window
        upcoming_tournament
    end

