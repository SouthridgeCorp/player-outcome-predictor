graph TD

    static_config1_file_1 --> static_config_1
    static_config1_file_2 --> static_config_1

    static_config2_file_1 --> static_config_2
    static_config2_file_2 --> static_config_2
    
    dynamic_input_1 --> ui_function_input_1
    static_config_1 --> ui_function_input_1
    
    dynamic_input_2 --> ui_function_input_2
    static_config_1 --> ui_function_input_2
    
    dynamic_input_3 --> ui_function_input_3
    static_config_2 --> ui_function_input_3
    
    subgraph static_config_files
    static_config1_file_1
    static_config1_file_2
    static_config2_file_1
    static_config2_file_2
    end
    
    subgraph static_configuration
    static_config_1
    static_config_2
    end
    
    subgraph dynamic_inputs
    dynamic_input_1
    dynamic_input_2
    dynamic_input_3
    end
    
    subgraph ui_function_inputs
    ui_function_input_1
    ui_function_input_2
    ui_function_input_3
    end
    
    style static_config_files fill:#f9f
    style static_configuration fill:#4f0
    style dynamic_inputs fill:#ff0
    style ui_function_inputs fill:#09f

