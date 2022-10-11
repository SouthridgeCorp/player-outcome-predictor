# player-outcome-predictor
Predictive modeling to forecast player outcomes over a T20 tournament

## Getting the data ready

### All IPL Matches
- Run `scripts/helpers/build_tournament_match_file.py`
- This script converts `scripts/helpers/resources/IPLMatches.csv` to a format which is acceptable by the app
- The output of the script is a csv list of the matches we know about and a list of tournaments we know about
- This script stores the output file in `resources/match_data/matches.csv` and `resources/match_data/tournaments.csv`



