graph LR
 
      subgraph StaticDataLayer
            StaticDataSources -- configures --> ReadStaticConfig
      end

      subgraph ConstraintsLayer
            ConstraintDefinition -- implements --> Constraint_1
            ConstraintDefinition -- implements --> Constraint_2
      end

      subgraph AllocationRecommendationLayer
            AllocationRecommendation_1 -- estimates --> Objective_Metric_1
            AllocationRecommendation_1 -- estimates --> Objective_Metric_2
            AllocationRecommendation_2 -- estimates --> Objective_Metric_1
            AllocationRecommendation_2 -- estimates --> Objective_Metric_2
      end

      subgraph AllocationRecommenderLayer
            ReadStaticConfig -- configures --> AllocationRecommender_1 
            ConstraintDefinition -- configures --> AllocationRecommender_1
            AllocationRecommender_1 -- produces --> Allocation_Recommendation_1
            ReadStaticConfig -- configures --> AllocationRecommender_2 
            ConstraintDefinition -- configures --> AllocationRecommender_2
            AllocationRecommender_2 -- produces --> Allocation_Recommendation_2
      end

      subgraph ObjectiveFunctionsLayer
            Objective_Metric_1 -- feeds --> Aggregate_Objective_Metric
            Objective_Metric_2 -- feeds --> Aggregate_Objective_Metric
            AllocationRecommender_1 -- minimizes --> Aggregate_Objective_Metric
            AllocationRecommender_2 -- minimizes --> Aggregate_Objective_Metric    
      end


      subgraph OrchestrationLayer
            Scenario -- configures --> TestOrchestrator
            Scenario -- configures --> RealTimeOrchestrator
            
            AllocationRecommender_1 -- called_by --> TestOrchestrator
            AllocationRecommender_2 -- called_by --> TestOrchestrator
            Aggregate_Objective_Metric -- feeds --> TestOrchestrator
            
            AllocationRecommender_1 -- called_by --> RealTimeOrchestrator
            AllocationRecommender_2 -- called_by --> RealTimeOrchestrator
            Aggregate_Objective_Metric -- feeds --> RealTimeOrchestrator
      end
      
      subgraph VisualizationLayer
            RealTimeOrchestrator -- generates --> Visualization
      end

      subgraph ScenarioGenerationLayer
            ReadStaticConfig -- configures --> ScenarioGenerator
            Dynamic_Input_1 -- feeds --> ScenarioGenerator
            Dynamic_Input_2 -- feeds --> ScenarioGenerator
            ScenarioGenerator -- generators --> Scenario
      end

      subgraph ValidationLayer
            ValidationRules -- configure --> Validator
            TestOrchestrator -- calls --> Validator
            Validator -- produces --> Assertions
      end

