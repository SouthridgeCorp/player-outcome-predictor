# player-outcome-predictor
Predictive modeling to forecast player outcomes over a T20 tournament

## Getting the data ready
Before running the app, input data must be prepared: 
- Run `scripts/helpers/parse_cricsheet_inputs.py`
- The `parse_cricsheet_inputs.py` script parses T20 match information from cricsheet and generates the datasets to be 
used by the predictor app  This script converts `scripts/helpers/resources/IPLMatches.csv` to a format which is acceptable by the app
- The output of the script is a csv list of the matches we know about and a list of tournaments we know about
- For detailed instructions on how to run the script and its expected inputs & outputs, please refer to 
`scripts/helpers/README_parse_cricsheet_inputs.md`


