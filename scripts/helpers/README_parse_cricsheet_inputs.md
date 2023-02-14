# What is the parse_cricsheet_inputs.py script?

The `parse_cricsheet_inputs.py` script:
- parses T20 match information from cricsheet  
- generates the datasets to be used by the predictor app  

# Pre-requisites for running this script:

1. This script works on JSON match data that has been downloaded from cricsheet (https://cricsheet.org/matches/) and
 the code is tightly coupled with the JSON format described here:
 https://cricsheet.org/format/json/#introduction-to-the-json-format. All these snapshots were taken on 11 Oct 2022.
2. Match JSONs are also available here: https://drive.google.com/drive/folders/1PqvK6boUEKu8qMWEBR2e-ca4xkTf6scJ
3. In order to execute this script, the input data will need to be prepared. See instructions below. 

## Preparing the data
The data can be prepared in two ways: 

### The Easy Way
Use this to quickly setup your test environment
- Download the file `cricsheet.zip` from Google Drive: 
- https://drive.google.com/file/d/1Iy5x8F2TbrWxlakhH1L1BvB9YyRLgIqn/view?usp=share_link
- Uncompress the zip file in the input folder you want to provide to your script (Note: the drive will all match 
folders under a folder called cricsheet)

### The Long Way
Use this if you want to pick and choose the files to experiment with

- Download the Tournament JSONs from the drive link provided above
- Uncompress each zip file, and ensure that the name of the uncompressed folder is the same as the name of the
tournament provided in main()
- Ensure all uncompressed directories live under `BASE_INPUT_DIR` (defined at the top of the script)
- Ensure that `BASE_OUTPUT_DIR` is where you want the outputs to be (defined at the top of the script)
- Edit the `main()` function below to include the tournaments to parse. Each tournament must have a key (which is
also the name of the directory under which the match JSONs live) and a full name.

# How to run the script?

- Ensure that the pre-requisite steps have been taken
- Change the working directory to the root from where your `BASE_OUTPUT_DIR` and `BASE_INPUT_DIR` are defined
- Run the script by executing:
`python scripts/helpers/parse_cricsheet_inputs.py`

# Script Output
The script generates the following outputs in `OUTPUT_DIR`:
- `tournaments.csv`: A listing of all tournaments parsed, including the first and last match dates we have info on
- `players.csv`: A listing of all players known by the universe of matches & tournaments parsed. The player key defined 
here is referenced in other matches & innings information.  
- A folder for each tournament, named `<<tournament_key>>` which includes the following:
  - `matches.csv`: A list of match related meta-data for each match in the tournmaent
  - `innings.csv`: A list of ball-by-ball outcomes for each match in the tournament
  - `playing_xi.csv`: A list of the playing xi per team for each match in the tournament

