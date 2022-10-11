import pandas as pd
import os


def find_start_date(df, tournament):
    newdf = df[df["tournament"] == tournament]
    start_date = newdf['date'].min()
    return start_date

def find_end_date(df, tournament):
    newdf = df[df["tournament"] == tournament]
    end_date = newdf['date'].max()
    return end_date

def read_all_matches(input_file = "scripts/helpers/resources/IPLMatches.csv",
                     output_dir = "data/generated/match_data"):
    base_dir = output_dir
    if not os.path.isdir(base_dir):
        os.makedirs(base_dir)

    all_matches = pd.read_csv(input_file)

    # Associate the tournament with the matches
    all_matches['tournament'] = all_matches['date'].apply(lambda x: "IPL-{}".format(x[-4:]))
    all_matches['date'] = pd.to_datetime(all_matches['date'], format='%d/%m/%Y')
    matches_file = "{}/matches.csv".format(base_dir)
    all_matches.to_csv(matches_file, index = False)

    # Set a start & end date of the tournament from the list of first & last matches
    tournaments = pd.DataFrame(all_matches['tournament'].unique(), columns=['tournament'])
    tournaments['start_date'] = [find_start_date(all_matches, x) for x in tournaments['tournament']]
    tournaments['end_date'] = [find_end_date(all_matches, x) for x in tournaments['tournament']]

    tournament_file = "{}/tournaments.csv".format(base_dir)
    tournaments.to_csv(tournament_file, index=False)
