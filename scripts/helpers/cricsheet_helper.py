import json
import logging
import os

import pandas as pd

# TODO: Fields to be parameterized
BASE_INPUT_DIR_DEFAULT = "data/downloaded/cricsheet/"
BASE_OUTPUT_DIR_DEFAULT = "data/generated/prod/match_data/cricsheet/"
VENUE_MAP_PATH = "scripts/helpers/resources/venue_mapping.csv"


class PlayerMap:
    """
    Utility class to help parse / update global player information.
    """

    def __init__(self):
        self.number_of_players = 0
        # This is a dict of dicts, with key = player key and value = dict of all player attributes known
        self.player_dict = {}
        # This is a perf optimisation, since the cricsheet data refers to player names and we need a quick way to
        # find the key for a player name
        self.player_name_reverse_map = {}

    def find_key_for_player_name(self, player_name):
        """
        Returns the key for a player name. Builds it out if it doesn't exist yet in the reverse map.
        :param player_name: The player name to look up
        :return: The key corresponding to the player name
        """
        if player_name in self.player_name_reverse_map.keys():
            return self.player_name_reverse_map[player_name]

        # Building out the keys
        split_names = player_name.split()
        key = ""
        for name_substring in split_names:
            key += name_substring[0]
        key += player_name[-1] + str(self.number_of_players)
        return key

    def insert_player_information(self, player_name, player_key=None):
        """
        Inserts player information into the map, and returns the key corresponding to the player.
        :param player_name: The name of the player to insert
        :param player_key: The player key to map the player too. If the key is None, a new entry is created.
        :return: The key corresponding to this entry
        """
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
        """
        Return the contents of this map as a pandas dataframe
        :return: The dataframe containing all the contents of this map
        """
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
    """
    Helper function which copies the specified key from the json object if the key exists, and sets it as a value
    in the target dictionary. If the key does not exist in the json object, then it sets a default value in the target
    dictionary.
    :param json_object: The json object to search for the specific key
    :param target_dict: The dictionary which will be updated with the key / value pair
    :param key_in_json: The name of the key to look for in the json object
    :param key_in_dict: The name of the key to set the value for in the tagret dictionary
    :param index: If index > -1, the function treats the json object as a list of jsons and queries the specified index
    :param is_player: If True, then the function will look to update the player_map with the values
    :param player_map: The global map of all players - must be defined if is_player=True. This map will be updated with
    new player information discovered.
    :return: None
    """
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
    """
    Parses the list of players from the input json list and sets the player information to be copied over
    :param player_json_list: The list of players to look through
    :param team: The team for which the players are enumerated
    :param match_key: The key for the match, to be included in the target list
    :param player_info: The target player list which is updated with the player information as a hash-map
    :param player_map: The global map of all players. This map will be updated with new player information discovered
    as the matches are parsed.
    :return: None
    """
    for player in player_json_list[team]:
        player_key = player_map.insert_player_information(player_name=player)
        player_info.append({"team": team, "match_key": match_key, "player_key": player_key})


def parse_innings_data(json_innings, match_key, innings_list, player_map):
    """
    Parses the innings object in the cricsheet json, and populates the innings list with a map of all related fields
    :param json_innings: The json innings object to parse
    :param match_key: The key of the match associated with this innings
    :param innings_list: The list of innings to populate
    :param player_map: The global map of all players. This map will be updated with new player information discovered
    as the matches are parsed.
    :return: None
    """
    inning_count = 0
    for inning in json_innings:
        inning_count += 1  # Ensure we keep track of the innings number
        team = inning["team"]

        # Get target runs & info if available
        target_map = {'target_runs': -1, 'target_overs': -1}
        if "target" in inning.keys():
            target = inning["target"]
            set_json_value_if_exists(target, target_map, "overs", "target_overs")
            set_json_value_if_exists(target, target_map, "runs", "target_runs")
            target_map['target_overs'] = int(target_map['target_overs'])

        over_count = -1
        for over_row in inning["overs"]:
            over_count += 1  # Ensure we keep track of the over number
            ball_number = 0

            for delivery in over_row["deliveries"]:
                ball_number += 1  # Ensure we keep track of the ball number

                # Set all the basic values for a delivery
                ball_map = {"match_key": match_key, "inning": inning_count, "over": over_count, "ball": ball_number,
                            "batting_team": team}
                ball_map.update(target_map)
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

                        direct_runout = 0
                        # ASSUMPTION: Let us assume that all run outs are direct, unless proven otherwise by the
                        # fielder count below
                        if ball_map["dismissal_kind"] == "run out":
                            direct_runout = 1

                        num_fielders = 0
                        if "fielders" in wicket.keys():
                            for fielder in wicket["fielders"]:
                                num_fielders += 1

                                if num_fielders == 1:
                                    # We only care about the first field for keeping records
                                    set_json_value_if_exists(fielder, ball_map, "name", "fielder",
                                                             is_player=True, player_map=player_map)

                                if num_fielders > 1:
                                    # ASSUMPTION: We assume that the presence of more than 1 fielder in a run-out
                                    # implies an indirect run out
                                    if direct_runout == 1:
                                        direct_runout = 0
                                    # We don't really care beyond 2 fielders for now, hence break
                                    break

                        ball_map["is_direct_runout"] = str(direct_runout)
                        # ASSUMPTION: We are only interested in 1 wicket per delivery
                        break
                else:
                    ball_map["is_wicket"] = 0
                    ball_map["dismissal_kind"] = ""
                    ball_map["player_dismissed"] = ""
                    ball_map["fielder"] = ""
                    ball_map["is_direct_runout"] = ""

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
    :param player_map: The global map of all players. This map will be updated with new player information discovered
    as the matches are parsed.
    :return: None
    """
    with open(input_file, 'r') as json_file:
        data = json_file.read()

    venue_mapping_df = pd.read_csv(VENUE_MAP_PATH)
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

        if "venue" in match_dict.keys():
            venue = match_dict["venue"]
            city = ""
            if "city" in match_dict.keys():
                city = match_dict["city"]

            query_string = f'venue == "{venue}"'

            if len(city) > 0:
                query_string += f'and city == "{city}"'

            mapped_venue_df = venue_mapping_df.query(query_string)
            if not mapped_venue_df.empty:
                mapped_venue = mapped_venue_df.iloc[0]['mapped_venue']
                logging.debug(f"Mapping {city}: {venue} to {mapped_venue}")
                match_dict['venue'] = mapped_venue

        set_json_value_if_exists(json_object["info"], match_dict, "season", "season")
        set_json_value_if_exists(json_object["info"], match_dict, "teams", "team1", index=0)
        set_json_value_if_exists(json_object["info"], match_dict, "teams", "team2", index=1)
        if "event" in json_object["info"]:
            set_json_value_if_exists(json_object["info"]["event"], match_dict, "match_number", "match_number")
            set_json_value_if_exists(json_object["info"]["event"], match_dict, "group", "group")
            set_json_value_if_exists(json_object["info"]["event"], match_dict, "stage", "stage")

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
        logging.debug(f"Ignoring match gender:{gender} type:{match_type}")


def parse_match_data(tournament_key, player_map, base_input_dir):
    """
    Goes through all the match JSONs associated with the tournament and creates the dataframes for matches, players and
    innings.
    :param player_map: The global map of all players. This map will be updated with new player information discovered
    as the matches are parsed.
    :param tournament_key: The key of the tournament
    :param base_input_dir: The base dir from where input can be sourced
    :return: None
    """
    input_directory = base_input_dir + tournament_key
    match_dict_list = []
    playing_xi_dict_list = []
    innings_list = []

    for filename in os.scandir(input_directory):
        if filename.is_file() and filename.path[-5:] == ".json":
            parse_json_match_data(filename.path, tournament_key, match_dict_list, playing_xi_dict_list, innings_list,
                                  player_map)
        else:
            logging.debug(f"Skipping non-json file {filename.path}")

    match_df = pd.DataFrame(data=match_dict_list)
    playing_xi_df = pd.DataFrame(data=playing_xi_dict_list)
    innings_df = pd.DataFrame(data=innings_list)
    return match_df, playing_xi_df, innings_df


def write_match_data(tournament_key, match_df, player_df, innings_df, base_output_dir):
    """
    Writes details related to the match (matches, players and innings) to their corresponding csv files.

    :param tournament_key: The key of the tournament, also used to build the directory structure
    :param match_df: The dataframe containing match information
    :param player_df: The dataframe containing playing XI information for the match
    :param innings_df: The dataframe containing ball by ball results for the match
    :param base_output_dir: The output directory where all output is written
    :return: None
    """
    output_dir = base_output_dir + tournament_key
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
    :return: None
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
    """
    Reads the global players file and builds out a map of all the information retrieved. This map can be updated by
    other data points and then finally be used to rewrite the cricsheet file.
    :param player_file: The full file path for player information
    :param player_map: The map which should be updated with the information read so far
    :return: None
    """
    if os.path.exists(player_file):
        player_df = pd.read_csv(player_file)
        player_list = player_df.to_dict('records')
        for row in player_list:
            player_map.insert_player_information(player_key=row["key"], player_name=row["name"])


def write_players_file(player_file, player_map):
    """
    Write the global player file
    :param player_file: The full file path for player information
    :param player_map: Details of the players to be documented
    :return: None
    """
    player_df = player_map.get_dataframe()
    player_df.to_csv(player_file, index=False)


def parse_data(tournament_key, tournament_name,
               base_input_dir=BASE_INPUT_DIR_DEFAULT, base_output_dir=BASE_OUTPUT_DIR_DEFAULT):
    """
    Parses & writes match, tournament and player data
    :param tournament_key: The key of the tournament
    :param tournament_name: The full name of the tournament
    :param base_input_dir: The directory where the input files exist
    :param base_output_dir: The base directory for storing the output
    :return: None
    """

    logging.info(f"Parsing ({tournament_key}) {tournament_name}")
    # read all details already available in the global players file
    player_file = base_output_dir + "/players.csv"
    player_map = PlayerMap()
    read_players_file(player_file, player_map)

    # parse the matches json and build out per match meta-data, playing xi data & innings data.
    match_df, playing_xi_df, innings_df = parse_match_data(tournament_key, player_map, base_input_dir)

    # Write per match data into the tournament specific directory
    write_match_data(tournament_key, match_df, playing_xi_df, innings_df, base_output_dir)

    # Write global player data
    write_players_file(player_file, player_map)

    # Write global tournament data
    tournament_file = base_output_dir + "/tournaments.csv"
    write_tournament_data(tournament_key, tournament_name, tournament_file, match_df["date"].min(),
                          match_df["date"].max())
