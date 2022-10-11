flowchart LR
    
    cluster_1_persona_1 --> |needs| need_1
    cluster_1_persona_2 --> |needs| need_2
    
    cluster_2_persona_1 --> |related_to| cluster_2_persona_2
    cluster_2_persona_2 --> |needs| need_2

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

    style cluster_1 fill:#FF8C00,stroke:#555,stroke-width:4px
    style cluster_2 fill:#FFD700,stroke:#333,stroke-width:4px
    style persona_needs fill:	#DC143C,stroke:#333,stroke-width:4px
