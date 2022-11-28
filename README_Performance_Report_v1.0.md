# Analysis for v1.0 Performance of the Application

## Predictive Simulator
We will us the International T20 season for 2022 as the test dataset on which we comment upon the 
current performance of the pipeline. We use this selection as we are more likely to find training data
for players in the ILT20 2023 using this selection.

For this test dataset, we train 2 models [Random Forest and Bayesian Inference] using
the "AND_selection" filter on matches going back to the beginning of 2022.

The Predictive Simulator is used to report error metrics for the following model configurations:
1. Match State Simulation: Statistical Simulator, Batter Runs Prediction: Statistical Simulator
2. Match State Simulation: Statistical Simulator, Batter Runs Prediction: Random Forest Classifier
3. Match State Simulation: Statistical Simulator, Batter Runs Prediction: Bayesian Inference Classifier

### Error Commentary - Match State Simulation: Statistical Simulator, Batter Runs Prediction: Statistical Simulator

### Error Commentary - Match State Simulation: Statistical Simulator, Batter Runs Prediction: Random Forest Classifier

### Error Commentary - Match State Simulation: Statistical Simulator, Batter Runs Prediction: Bayesian Inference Classifier

### Conclusion

## Tournament Simulator - ILT20 2023 Season

To demonstrate the usage of this application for simulating player rewards for an upcoming tournament,
we have re-formatted the input playing xi's provided [here](https://docs.google.com/spreadsheets/d/1Y4rOdm6wgdAZnnaTHfNS1J5zFuXViPd8JWVwc8sR5HI/edit#gid=0)
and converted it into an example tournament input which is checked in under resources/prod/app_config/tournament_simulator/ilt20

The following assumptions are made in this input file:
1. The venues are randomly selected between the 3 known venues for the ILT20 2023
2. 2 of the 66 players do not have any historical data available from Cricsheet. These players can be identified in the example inputs.
3. 50 scenarios are generated for the evolution of the tournament. This can be modified by changing the config setting.

### Simulation Commentary - Match State Simulation: Statistical Simulator, Batter Runs Prediction: Statistical Simulator

### Simulation Commentary - Match State Simulation: Statistical Simulator, Batter Runs Prediction: Random Forest Classifier

### Simulation Commentary - Match State Simulation: Statistical Simulator, Batter Runs Prediction: Bayesian Inference Classifier

### Conclusion


