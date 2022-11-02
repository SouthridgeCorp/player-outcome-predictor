import pandas as pd
from rewards_configuration.rewards_configuration import RewardsConfiguration


def get_bowler_penalty_for_runs(row):
    total_runs = row["total_runs"]
    batter_runs = row["batter_runs"]
    extras = row["extras"]
    wides = row["wides"]
    no_ball = row["noballs"]
    non_boundary = row["non_boundary"]

    outcome_index = ""
    if total_runs == 0:
        outcome_index = "0"
    else:
        # Assumption: If a batsman runs on a no-ball or wide, the no-ball takes precedence
        if extras > 0:
            if no_ball == 1:
                if batter_runs > 0:
                    outcome_index += f"{batter_runs}b,"
                if extras > 0:
                    outcome_index += f"{extras}b,"
                outcome_index = f"nb"
            elif wides == 1:
                outcome_index = f"{total_runs}-w"
            else:
                outcome_index = f"{total_runs}-oe"
        else:
            outcome_index = f"{total_runs}-b"
    return outcome_index


def bowling_outcome(row):
    total_runs = row["total_runs"]
    batter_runs = row["batter_runs"]
    extras = row["extras"]
    is_wicket = row["is_wicket"]
    dismissal_kind = row["dismissal_kind"]
    is_direct_runout = row["is_direct_runout"]
    wides = row["wides"]
    no_ball = row["noballs"]

    outcome_index = ""

    if batter_runs > 0:
        outcome_index += f"{batter_runs}-b,"

    if extras > 0:
        outcome_index += f"{extras}"
        if no_ball == 1:
            outcome_index += "-nb,"
        elif wides == 1:
            outcome_index += "-w,"
        else:
            outcome_index += "-oe,"

    if is_wicket == 1:
        outcome_index += "W"

        if dismissal_kind == "stumped":
            outcome_index += "-bs"
        elif dismissal_kind == "caught":
            outcome_index += "-bc"
        elif dismissal_kind == "run out":
            if (pd.isna(is_direct_runout)) or is_direct_runout == 0:
                outcome_index += "-idro"
            else:
                outcome_index += "-dro"
        elif (dismissal_kind == "bowled") or (dismissal_kind == "caught and bowled"):
            outcome_index += "-b"
        else:
            outcome_index += "-others"

    if outcome_index == "":
        outcome_index = "0"

    return outcome_index.rstrip(",")

def set_bowling_base_rewards(row, rewards_configuration: RewardsConfiguration):
    total_runs = row["total_runs"]
    wides = row["wides"]
    no_ball = row["noballs"]

    bowling_rewards = rewards_configuration.get_bowling_base_rewards_for_runs(total_runs)

    if no_ball == 1:
        bowling_rewards += rewards_configuration.get_bowling_base_rewards_for_extras(RewardsConfiguration.NO_BALL)

    if wides == 1:
        bowling_rewards += rewards_configuration.get_bowling_base_rewards_for_extras(RewardsConfiguration.WIDE)

    return bowling_rewards


def batting_outcome(row):
    batter_runs = row["batter_runs"]
    is_wicket = row["is_wicket"]
    extras = row["extras"]

    batter = row['batter']
    player_dismissed = row['player_dismissed']

    batter_outcome_index = ""
    non_striker_outcome_index = "0"
    if batter_runs > 0:
        batter_outcome_index += f"{batter_runs}-b,"

    if is_wicket == 1:
        if player_dismissed == batter:
            batter_outcome_index += "W"
        else:
            non_striker_outcome_index = "W"

    if batter_outcome_index == "" and extras > 0:
        batter_outcome_index = "E"
    if batter_outcome_index == "":
        batter_outcome_index = "0"

    return batter_outcome_index.rstrip(","), non_striker_outcome_index


def fielding_outcome(row):
    is_wicket = row["is_wicket"]
    dismissal_kind = row["dismissal_kind"]
    is_direct_runout = row["is_direct_runout"]
    fielder = row['fielder']

    fielder_outcome_index = "nfo"

    if pd.notna(fielder):
        if is_wicket == 1:
            if dismissal_kind == "stumped":
                fielder_outcome_index = "W-bs"
            elif dismissal_kind == "caught":
                fielder_outcome_index = "W-bc"
            elif dismissal_kind == "run out":
                if (pd.isna(is_direct_runout)) or is_direct_runout == 0:
                    fielder_outcome_index = "W-idro"
                else:
                    fielder_outcome_index = "W-dro"

    return fielder_outcome_index

def set_fielding_outcome(row, rewards_configuration: RewardsConfiguration):
    is_wicket = row["is_wicket"]
    dismissal_kind = row["dismissal_kind"]
    is_direct_runout = row["is_direct_runout"]
    fielder = row['fielder']

    fielder_reward = 0

    if pd.notna(fielder):
        if is_wicket == 1:
            if dismissal_kind == "stumped":
                fielder_reward = rewards_configuration.\
                    get_fielding_base_rewards_for_dismissal(RewardsConfiguration.FIELDING_STUMP)
            elif dismissal_kind == "caught":
                fielder_reward = rewards_configuration. \
                    get_fielding_base_rewards_for_dismissal(RewardsConfiguration.FIELDING_CATCH)
            elif dismissal_kind == "run out":
                if (pd.isna(is_direct_runout)) or is_direct_runout == 0:
                    fielder_reward = rewards_configuration. \
                        get_fielding_base_rewards_for_dismissal(RewardsConfiguration.FIELDING_IDRO)
                else:
                    fielder_reward = rewards_configuration. \
                        get_fielding_base_rewards_for_dismissal(RewardsConfiguration.FIELDING_DRO)
    return fielder_reward

    return fielder_outcome_index

def set_batting_base_rewards(row, rewards_configuration: RewardsConfiguration):
    batter_runs = row["batter_runs"]
    is_wicket = row["is_wicket"]
    extras = row["extras"]

    batter = row['batter']
    player_dismissed = row['player_dismissed']

    batter_rewards = rewards_configuration.get_batting_base_rewards_for_runs(batter_runs)
    non_striker_rewards = 0

    if is_wicket == 1:
        dismissal_reward = rewards_configuration.get_batting_base_rewards_for_dismissal()
        if player_dismissed == batter:
            batter_rewards += dismissal_reward
        else:
            non_striker_rewards = dismissal_reward

    return batter_rewards, non_striker_rewards

def set_bowling_bonus_wickets(row, rewards_configuration: RewardsConfiguration):
    bowling_bonus_wickets = 0

    wickets_taken = row['wickets_taken']
    if pd.notna(wickets_taken) and wickets_taken > 0:
        bowling_bonus_wickets = rewards_configuration.get_bowling_rewards_for_wickets(wickets_taken)

    return bowling_bonus_wickets