# Tournament Simulator - Configuration
The tournament simulator currently accepts file based tournament configuration based on which it simulates outcomes for 
an IPL like tournament. Details on how the simulator works and how to configure it are provided below. 

## How does the simulator work? 
* The Tournament Simulator currently simulates IPL style tournaments, with the following stages:
  - Group: All teams play against each other
  - Qualifier 1: The top 2 teams after the group stages play, the winner goes to the Finals
  - Eliminator: Teams 3 & 4 from the top after the group stages play, the loser is eliminated
  - Qualifier 2: The winner of the Eliminator & the loser of Qualifier 1 play, the winners goes to the finals
  - Final: The Winners of Qualifier 1 and Qualifier 2 play
* The simulator currently accepts two configuration files (in csv format):
  * Match config, which outlines all the matches to be played, their venues and teams. The teams for the non-group 
  rounds should be blank
  * Player config, which maps each team to its playing XI. We assume that each team has the same playing XI for the 
  duration of the tournament.
  * __Note__: The teams, players and venues must be a part of the overall historical match dataset, else the simulator 
  will throw an error
  * Sample match & player config simulating an IPL are available here:
    * Match config: *resources/prod/app_config/tournament_simulator/example_tournament.csv*
    * Player config: *resources/prod/app_config/tournament_simulator/example_playing_xi.csv*
* The simulator relies on the training window to build the player universe and calculate featured players. The training 
window must include all the players who are participating in the simulated tournament.

## Configuring the match simulator
* The match simulator configuration is defined in config.toml in .streamlit, and supports the following fields:
  ```
  [player_outcome_predictor.tournament_simulator]
  number_of_scenarios=4
  data_path="resources/prod/app_config/tournament_simulator"
  matches_file_name='example_tournament.csv'
  playing_xi_file_name='example_playing_xi.csv''
  ```
  where:
  * *number_of_scenarios* = The total number of tournament scenarios to run, currently capped at 99. 
  * *data_path* = The director where the file config for the simulator resides 
  * *matches_file_name* = the name of the match config file, expected to be present in `data_path`
  * *playing_xi_file_name* = the name of the playing xi file name, expected to be present in `data_path`