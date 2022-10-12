import os
import pandas as pd
import json

BASE_INPUT_DIR = "scripts/helpers/resources/cricsheet/"
BASE_OUTPUT_DIR = "data/generated/match_data/cricsheet/"


def set_json_value_if_exists(json_object, match_dict, key_in_json, key_in_dict, index=-1):
    if key_in_json in json_object.keys():
        if index == -1:
            value = json_object[key_in_json]
        else:
            value = json_object[key_in_json][index]
        match_dict[key_in_dict] = value
    else:
        match_dict[key_in_dict] = ""


def parse_player_data(json_object, team, match_key, player_info):
    for player in json_object[team]:
        player_info.append({"team": team, "match_key": match_key, "player_name": player})


def parse_json_match_data(input_file, tournament_key, match_dict_list, player_dict_list):
    with open(input_file, 'r') as json_file:
        data = json_file.read()
    json_object = json.loads(data)
    gender = json_object["info"]["gender"]
    match_type = json_object["info"]["match_type"]

    match_dict = {}

    if gender == "male" and match_type == "T20":
        match_dict["key"] = input_file.split("/")[-1][:-5]
        match_dict["tournament_key"] = tournament_key
        set_json_value_if_exists(json_object["info"], match_dict, "city", "city")
        set_json_value_if_exists(json_object["info"], match_dict, "dates", "date", index=0)
        set_json_value_if_exists(json_object["info"], match_dict, "player_of_match", "player_of_match", index=0)
        set_json_value_if_exists(json_object["info"], match_dict, "venue", "venue")
        set_json_value_if_exists(json_object["info"], match_dict, "season", "season")

        set_json_value_if_exists(json_object["info"], match_dict, "teams", "team1", index=0)
        set_json_value_if_exists(json_object["info"], match_dict, "teams", "team2", index=1)
        set_json_value_if_exists(json_object["info"]["toss"], match_dict, "winner", "toss_winner")
        set_json_value_if_exists(json_object["info"]["toss"], match_dict, "decision", "toss_decision")

        set_json_value_if_exists(json_object["info"]["outcome"], match_dict, "winner", "winner")
        set_json_value_if_exists(json_object["info"]["outcome"], match_dict, "result", "result_if_no_winner")
        set_json_value_if_exists(json_object["info"]["outcome"], match_dict, "method", "method")
        set_json_value_if_exists(json_object["info"]["outcome"], match_dict, "eliminator", "eliminator")
        set_json_value_if_exists(json_object["info"]["outcome"], match_dict, "bowl_out", "bowl_out")

        if "by" in json_object["info"]["outcome"].keys():
            for key, value in json_object["info"]["outcome"]["by"].items():
                match_dict["result"] = key
                match_dict["result_margin"] = value

        parse_player_data(json_object["info"]["players"], match_dict["team1"], match_dict["key"], player_dict_list)
        match_dict_list.append(match_dict)
    else:
        print("Ignoring match gender:{} type:{}".format(gender, match_type))


def parse_match_data(tournament_key):
    input_directory = BASE_INPUT_DIR + tournament_key
    match_dict_list = []
    player_dict_list = []

    for filename in os.scandir(input_directory):
        if filename.is_file():
            try:
                parse_json_match_data(filename.path, tournament_key, match_dict_list, player_dict_list)
            except:
                print("Could not parse file {}".format(filename.path))

    match_df = pd.DataFrame(data=match_dict_list)
    player_df = pd.DataFrame(data=player_dict_list)
    return match_df, player_df


def write_match_data(tournament_key, match_df, player_df):
    output_dir = BASE_OUTPUT_DIR + tournament_key
    if not os.path.isdir(output_dir):
        os.makedirs(output_dir)

    match_df.to_csv(output_dir + "/matches.csv", index=False)
    player_df.to_csv(output_dir + "/players.csv", index=False)



def write_tournament_data(tournament_key, tournament_name, tournament_file, tournament_start, tournament_end):
    if not os.path.exists(tournament_file):
        column_list = ["key", "name", "first_match_date", "last_match_date"]
        tournament_df = pd.DataFrame(columns=column_list)
    else:
        tournament_df = pd.read_csv(tournament_file)

    if tournament_key not in tournament_df["key"].values:
        tournament_dict = [{"key": tournament_key,
                            "name": tournament_name}]
        new_tournament_df = pd.DataFrame(data=tournament_dict)
        tournament_df = pd.concat([tournament_df, new_tournament_df], ignore_index=True)

    tournament_df.loc[(tournament_df["key"] == tournament_key), "first_match_date"] = tournament_start
    tournament_df.loc[(tournament_df["key"] == tournament_key), "last_match_date"] = tournament_end

    tournament_df.to_csv(tournament_file, index=False)


def parse_data(tournament_key, tournament_name, tournament_file):
    match_df, player_df = parse_match_data(tournament_key)
    write_match_data(tournament_key, match_df, player_df)

    write_tournament_data(tournament_key, tournament_name, tournament_file,
                          match_df["date"].min(), match_df["date"].max())


def main():
    parse_data("t20s", "International T20s", BASE_OUTPUT_DIR + "tournaments.csv")
    parse_data("apl", "Afghanistan Premier League", BASE_OUTPUT_DIR + "tournaments.csv")
    parse_data("bbl", "Big Bash League", BASE_OUTPUT_DIR + "tournaments.csv")
    parse_data("bpl", "Bangladesh Premier League", BASE_OUTPUT_DIR + "tournaments.csv")


main()
