flowchart LR
    
    cluster_1_persona_1 --> |needs| need_1
    cluster_1_persona_2 --> |needs| need_2
    cluster_1_persona_2 --> |needs| new_need_2
    
    cluster_2_persona_1 --> |related_to| cluster_2_persona_2
    cluster_2_persona_1 --> |needs| new_need_1
    cluster_2_persona_2 --> |needs| need_2
    
    need_1 --> |met_by| computational_model_current
    need_2 --> |no_longer_met_by| computational_model_current
    
    need_2 --> |can_be_met_by| computational_model_next
    new_need_1 --> |can_be_met_by| computational_model_next
    new_need_2 --> |can_be_met_by| computational_model_next

    subgraph cluster_1
        cluster_1_persona_1
        cluster_1_persona_2
    end
    
    subgraph cluster_2
        cluster_2_persona_1
        cluster_2_persona_2
    end
    
    subgraph persona_needs
        need_1
        need_2
    end
    
    subgraph persona_needs_new
        new_need_1
        new_need_2
    end
    
    subgraph current_major_version
        computational_model_current
    end
    
    subgraph next_major_version
        computational_model_next
    end

    style cluster_1 fill:#FF8C00,stroke:#555,stroke-width:4px
    style cluster_2 fill:#FFD700,stroke:#333,stroke-width:4px
    style persona_needs fill:#DC143C,stroke:#333,stroke-width:4px
    style current_major_version fill:#9ACD32,stroke:#333,stroke-width:4px
    style next_major_version fill:#AFEEEE,stroke:#333,stroke-width:4px
    style persona_needs_new fill:#32CD32,stroke:#333,stroke-width:4px
 
