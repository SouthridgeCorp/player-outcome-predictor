import os
import pandas as pd
import json

# Note: PLEASE READ README_parse_cricsheet_inputs.md before running this file.
#


BASE_INPUT_DIR = "data/downloaded/cricsheet/"
BASE_OUTPUT_DIR = "data/generated/match_data/cricsheet/"

class PlayerMap:
    def __init__(self):
        self.number_of_players = 0
        self.player_dict = {}
        self.player_name_reverse_map = {}

    def find_key_for_player_name(self, player_name):
        if player_name in self.player_name_reverse_map.keys():
            return self.player_name_reverse_map[player_name]
        split_names = player_name.split()
        key = ""
        for name_substr in split_names:
            key += name_substr[0]
        key += player_name[-1] + str(self.number_of_players)
        return key

    def insert_player_information(self, player_name, player_key=None):
        if player_key is None:
            key = self.find_key_for_player_name(player_name)
        else:
            key = player_key
        if key not in self.player_dict.keys():
            self.number_of_players += 1

        self.player_dict[key] = {"key": key, "name": player_name}
        self.player_name_reverse_map[player_name] = key
        return key

    def get_dataframe(self):
        player_list = []

        if self.number_of_players == 0:
            column_list = ["key", "name"]
            player_df = pd.DataFrame(columns=column_list)
        else:
            for key in self.player_dict:
                player_list.append(self.player_dict[key])
            player_df = pd.DataFrame(data=player_list)

        return player_df




def set_json_value_if_exists(json_object, target_dict, key_in_json, key_in_dict, index=-1,
                             is_player=False, player_map=None):
    '''
    Helper function which copies the specified key from the json object if the key exists, and sets it as a value
    in the target dictionary. If the key does not exist in the json object, then it sets a default value in the target
    dictionary.
    :param json_object: The json object to search for the specific key
    :param target_dict: The dictionary which will be updated with the key / value pair
    :param key_in_json: The name of the key to look for in the json object
    :param key_in_dict: The name of the key to set the value for in the tagret dictionary
    :param index: If index > -1, the function treats the json object as a list of jsons and queries the specified index
    :return:
    '''
    if key_in_json in json_object.keys():
        if index == -1:
            value = json_object[key_in_json]
        else:
            value = json_object[key_in_json][index]

        if is_player and player_map is not None:
            key = player_map.insert_player_information(value)
            value = key
        target_dict[key_in_dict] = value
    else:
        target_dict[key_in_dict] = ""

def parse_player_data(player_json_list, team, match_key, player_info, player_map):
    '''
    Parses the list of players from the input json list and sets the player information to be copied over
    :param player_json_list: The list of players to look through
    :param team: The team for which the players are enumerated
    :param match_key: The key for the match, to be included in the target list
    :param player_info: The target player list which is updated with the player information as a hash-map
    :return:
    '''
    for player in player_json_list[team]:
        player_key = player_map.insert_player_information(player_name = player)
        player_info.append({"team": team, "match_key": match_key, "player_key": player_key})


def parse_innings_data(json_innings, match_key, innings_list, player_map):
    '''
    Parses the innings object in the cricsheet json, and populates the innings list with a map of all related fields
    :param json_innings: The json innings object to parse
    :param match_key: The key of the match associated with this innings
    :param innings_list: The list of innings to populate
    :return:
    '''
    inning_count = 0
    for inning in json_innings:
        inning_count += 1  # Ensure we keep track of the innings number
        team = inning["team"]
        over_count = -1
        for over_row in inning["overs"]:
            over_count += 1  # Ensure we keep track of the over number
            over_number = over_row["over"]
            ball_number = 0

            for delivery in over_row["deliveries"]:
                ball_number += 1  # Ensure we keep track of the ball number

                # Set all the basic values for a delivery
                ball_map = {"match_key": match_key, "inning": inning_count, "over": over_count, "ball": ball_number,
                            "batting_team": team}
                set_json_value_if_exists(delivery, ball_map, "batter", "batter", is_player=True, player_map=player_map)
                set_json_value_if_exists(delivery, ball_map, "bowler", "bowler", is_player=True, player_map=player_map)
                set_json_value_if_exists(delivery, ball_map, "non_striker", "non_striker",
                                         is_player=True, player_map=player_map)
                set_json_value_if_exists(delivery["runs"], ball_map, "batter", "batter_runs")
                set_json_value_if_exists(delivery["runs"], ball_map, "extras", "extras")
                set_json_value_if_exists(delivery["runs"], ball_map, "total", "total_runs")
                set_json_value_if_exists(delivery["runs"], ball_map, "non_boundary", "non_boundary")

                # Set the wicket details
                if "wickets" in delivery.keys():
                    ball_map["is_wicket"] = 1
                    for wicket in delivery["wickets"]:
                        set_json_value_if_exists(wicket, ball_map, "kind", "dismissal_kind")
                        set_json_value_if_exists(wicket, ball_map, "player_out", "player_dismissed",
                                                 is_player=True, player_map=player_map)
                        if "fielders" in wicket.keys():
                            for fielder in wicket["fielders"]:
                                set_json_value_if_exists(fielder, ball_map, "name", "fielder",
                                                         is_player=True, player_map=player_map)
                                # ASSUMPTION: We are only interested in 1 fielder per wicket
                                break
                        # ASSUMPTION: We are only interested in 1 wicket per delivery
                        break
                else:
                    ball_map["is_wicket"] = 0
                    ball_map["dismissal_kind"] = ""
                    ball_map["player_dismissed"] = ""
                    ball_map["fielder"] = ""

                # Get all information on extras
                if "extras" in delivery.keys():
                    set_json_value_if_exists(delivery["extras"], ball_map, "byes", "byes")
                    set_json_value_if_exists(delivery["extras"], ball_map, "legbyes", "legbyes")
                    set_json_value_if_exists(delivery["extras"], ball_map, "noballs", "noballs")
                    set_json_value_if_exists(delivery["extras"], ball_map, "penalty", "penalty")
                    set_json_value_if_exists(delivery["extras"], ball_map, "wides", "wides")
                else:
                    ball_map["byes"] = ''
                    ball_map["legbyes"] = ''
                    ball_map["noballs"] = ''
                    ball_map["penalty"] = ''
                    ball_map["wides"] = ''

                innings_list.append(ball_map)


def parse_json_match_data(input_file, tournament_key, match_dict_list, playing_xi_dict_list, innings_list, player_map):
    """
    Parses all information (matches, innings, players) for a specific match.
    :param input_file: The file name containing the JSON representation of the match
    :param tournament_key: The key of the tournament
    :param match_dict_list: The list to append with the match details (as a map)
    :param playing_xi_dict_list: The list to append with the player details (as a map)
    :param innings_list: The list to append with the innings details (as a map)
    :return: None
    """
    with open(input_file, 'r') as json_file:
        data = json_file.read()
    json_object = json.loads(data)
    gender = json_object["info"]["gender"]
    match_type = json_object["info"]["match_type"]

    match_dict = {}

    if gender == "male" and match_type == "T20":
        match_dict["key"] = input_file.split("/")[-1][:-5]
        # Get Match level meta-data
        match_dict["tournament_key"] = tournament_key
        set_json_value_if_exists(json_object["info"], match_dict, "city", "city")
        set_json_value_if_exists(json_object["info"], match_dict, "dates", "date", index=0)
        set_json_value_if_exists(json_object["info"], match_dict, "player_of_match",
                                 "player_of_match", index=0, is_player=True, player_map=player_map)
        set_json_value_if_exists(json_object["info"], match_dict, "venue", "venue")
        set_json_value_if_exists(json_object["info"], match_dict, "season", "season")
        set_json_value_if_exists(json_object["info"], match_dict, "teams", "team1", index=0)
        set_json_value_if_exists(json_object["info"], match_dict, "teams", "team2", index=1)

        # Who won the toss and what did they do?
        set_json_value_if_exists(json_object["info"]["toss"], match_dict, "winner", "toss_winner")
        set_json_value_if_exists(json_object["info"]["toss"], match_dict, "decision", "toss_decision")

        # Who won the match & how?
        set_json_value_if_exists(json_object["info"]["outcome"], match_dict, "winner", "winner")
        set_json_value_if_exists(json_object["info"]["outcome"], match_dict, "result", "result_if_no_winner")
        set_json_value_if_exists(json_object["info"]["outcome"], match_dict, "method", "method")
        set_json_value_if_exists(json_object["info"]["outcome"], match_dict, "eliminator", "eliminator")
        set_json_value_if_exists(json_object["info"]["outcome"], match_dict, "bowl_out", "bowl_out")
        if "by" in json_object["info"]["outcome"].keys():
            for key, value in json_object["info"]["outcome"]["by"].items():
                match_dict["result"] = key
                match_dict["result_margin"] = value

        match_dict_list.append(match_dict)

        # Pull out the playing XI
        parse_player_data(json_object["info"]["players"], match_dict["team1"], match_dict["key"],
                          playing_xi_dict_list, player_map)
        parse_player_data(json_object["info"]["players"], match_dict["team2"], match_dict["key"],
                          playing_xi_dict_list, player_map)

        # Pull out the ball-by-ball information
        if "innings" in json_object.keys():
            parse_innings_data(json_object["innings"], match_dict["key"], innings_list, player_map)
    else:
        print("Ignoring match gender:{} type:{}".format(gender, match_type))


def parse_match_data(tournament_key, player_map):
    """
    Goes through all the match JSONs associated with the tournament and creates the dataframes for matches, players and
    innings.
    :param tournament_key: The key of the tournament
    :return: None
    """
    input_directory = BASE_INPUT_DIR + tournament_key
    match_dict_list = []
    playing_xi_dict_list = []
    innings_list = []

    for filename in os.scandir(input_directory):
        if filename.is_file() and filename.path[-5:] == ".json":
            parse_json_match_data(filename.path, tournament_key, match_dict_list, playing_xi_dict_list, innings_list,
                                  player_map)
        else:
            print("Skipping non-json file {}".format(filename.path))

    match_df = pd.DataFrame(data=match_dict_list)
    playing_xi_df = pd.DataFrame(data=playing_xi_dict_list)
    innings_df = pd.DataFrame(data=innings_list)
    return match_df, playing_xi_df, innings_df


def write_match_data(tournament_key, match_df, player_df, innings_df):
    """
    Writes details related to the match (matches, players and innings) to their corresponding csv files.

    :param tournament_key: The key of the tournament, also used to build the directory structure
    :param match_df: The dataframe containing match information
    :param player_df: The dataframe containing playing XI information for the match
    :param innings_df: The dataframe containing ball by ball results for the match
    :return: None
    """
    output_dir = BASE_OUTPUT_DIR + tournament_key
    if not os.path.isdir(output_dir):
        os.makedirs(output_dir)

    match_df.to_csv(output_dir + "/matches.csv", index=False)
    player_df.to_csv(output_dir + "/playing_xi.csv", index=False)
    innings_df.to_csv(output_dir + "/innings.csv", index=False)


def write_tournament_data(tournament_key, tournament_name, tournament_file, tournament_start, tournament_end):
    """
    Writes details related to the tournament to the tournament file. If the tournament already exists,
    updates its details.
    :param tournament_key: The tournament key
    :param tournament_name: The full name of the tournamanet
    :param tournament_file: The file to write to
    :param tournament_start: The date of the first match in the tournament series
    :param tournament_end: The date of the last match in the tournament series
    :return:
    """
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


def read_players_file(player_file, player_map):
    if os.path.exists(player_file):
        player_df = pd.read_csv(player_file)
        player_list = player_df.to_dict('records')
        for row in player_list:
            player_map.insert_player_information(player_key=row["key"], player_name=row["name"])


def write_players_file(player_file, player_map):
    player_df = player_map.get_dataframe()
    player_df.to_csv(player_file, index=False)


def parse_data(tournament_key, tournament_name):
    """
    Parses & writes match & tournament data
    :param tournament_key: The key of the tournament
    :param tournament_name: The full name of the tournament
    :return: None
    """

    tournament_file = BASE_OUTPUT_DIR + "tournaments.csv"
    player_file = BASE_OUTPUT_DIR + "players.csv"

    player_map = PlayerMap()
    read_players_file(player_file, player_map)
    match_df, playing_xi_df, innings_df = parse_match_data(tournament_key, player_map)
    write_match_data(tournament_key, match_df, playing_xi_df, innings_df)

    write_tournament_data(tournament_key, tournament_name, tournament_file,
                          match_df["date"].min(), match_df["date"].max())

    write_players_file(player_file, player_map)


def main():
    """
    The main function - Tournament list below must be updated before running the script.
    :return: None
    """
    parse_data("t20s", "International T20s")
    parse_data("apl", "Afghanistan Premier League")
    parse_data("bbl", "Big Bash League")
    parse_data("bpl", "Bangladesh Premier League")
    parse_data("cpl", "Caribbean Premier League")
    parse_data("ctc", "CSA T20 Challenge")
    parse_data("ipl", "Indian Premier League")
    parse_data("lpl", "Lanka Premier League")
    parse_data("psl", "Pakistan Super League")
    parse_data("ssm", "Super Smash")
    parse_data("ntb", "T20 Blast")
    parse_data("msl", "Mzansi Super League")


main()
