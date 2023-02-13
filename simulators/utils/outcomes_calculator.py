import pandas as pd
from rewards_configuration.rewards_configuration import RewardsConfiguration


def get_bowler_outcome_label_for_runs(row):
    """
    Calculates the bowler outcome string for runs
    """
    total_runs = row["total_runs"]
    batter_runs = row["batter_runs"]
    extras = row["extras"]
    wides = row["wides"]
    no_ball = row["noballs"]

    outcome_index = ""
    if total_runs == 0:
        outcome_index = "0"
    else:
        # Assumption: If a batsman runs on a no-ball or wide, the no-ball takes precedence
        if extras > 0:
            if no_ball >= 1:
                if batter_runs > 0:
                    outcome_index += f"{batter_runs}b,"
                if extras > 0:
                    outcome_index += f"{extras}b,"
                outcome_index = f"nb"
            elif wides >= 1:
                outcome_index = f"{total_runs}-w"
            else:
                outcome_index = f"{total_runs}-oe"
        else:
            outcome_index = f"{total_runs}-b"
    return outcome_index


def get_bowling_outcome_label(row):
    """
    Calculate the bowling outcome label for a ball / innings. Labels can be 1-b, W-idro etc.
    """
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
        if no_ball >= 1:
            outcome_index += "-nb,"
        elif wides >= 1:
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


def get_bowling_base_rewards(row, rewards_configuration: RewardsConfiguration):
    """
    Gets the bowling base rewards for an outcome
    """
    total_runs = row["total_runs"]
    wides = row["wides"]
    no_ball = row["noballs"]
    # Calculate byes & legbyes
    # TODO: Remove the checks below once the tournament simulator starts simulating byes & legbyes
    byes = 0
    legbyes = 0
    if 'byes' in list(row.axes[0]):
        byes = row['byes']
    if 'legbyes' in list(row.axes[0]):
        legbyes = row['legbyes']

    if byes > 0 or legbyes > 0:
        # Bowler gets no penalty or rewards for byes & legbyes
        bowling_rewards = 0
    else:
        bowling_rewards = rewards_configuration.get_bowling_base_rewards_for_runs(total_runs)

    if no_ball >= 1:
        bowling_rewards += rewards_configuration.get_bowling_base_rewards_for_extras(RewardsConfiguration.NO_BALL)

    if wides >= 1:
        bowling_rewards += rewards_configuration.get_bowling_base_rewards_for_extras(RewardsConfiguration.WIDE)

    return bowling_rewards


def get_batting_outcome_labels(row):
    """
    Calculate the batting outcome label for a ball / innings. Labels can be 1-b, W etc.
    """
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


def get_fielding_outcome_labels(row):
    """
    Calculate the fielding outcome label for a ball / innings. Labels can be W-bs, W-idro etc.
    """
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


def get_outcome_labels(row):
    """
    Get all the labels corresponding to the outcomes row
    """
    bowling_outcomes = get_bowling_outcome_label(row)
    batting_outcomes, non_striker_outcomes = get_batting_outcome_labels(row)
    fielding_outcomes = get_fielding_outcome_labels(row)

    return bowling_outcomes, batting_outcomes, non_striker_outcomes, fielding_outcomes


def get_fielding_base_rewards(row, rewards_configuration: RewardsConfiguration):
    """
    Gets the fielding base rewards for an outcome
    """
    is_wicket = row["is_wicket"]
    dismissal_kind = row["dismissal_kind"]
    is_direct_runout = row["is_direct_runout"]
    fielder = row['fielder']

    fielder_reward = 0

    if pd.notna(fielder):
        if is_wicket == 1:
            if dismissal_kind == "stumped":
                fielder_reward = rewards_configuration. \
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


def get_batting_base_rewards(row, rewards_configuration: RewardsConfiguration):
    """
    Gets the batting base rewards for an outcome
    """
    batter_runs = row["batter_runs"]
    is_wicket = row["is_wicket"]
    extras = row["extras"]

    batter = row['batter']
    player_dismissed = row['player_dismissed']

    batter_rewards = rewards_configuration.get_batting_base_rewards_for_runs(batter_runs)
    if (extras > 0) and (batter_rewards < 0):
        # Batters don't get any penalties or rewards for extras (even if there were batter runs in those extras)
        batter_rewards = 0

    non_striker_rewards = 0

    if is_wicket == 1:
        dismissal_reward = rewards_configuration.get_batting_base_rewards_for_dismissal()
        if player_dismissed == batter:
            batter_rewards += dismissal_reward
        else:
            non_striker_rewards = dismissal_reward

    return batter_rewards, non_striker_rewards


def get_base_rewards(row, rewards_configuration):
    """
    Get all the base rewards for the player specified by the row
    """
    batter_rewards, non_striker_rewards = get_batting_base_rewards(row, rewards_configuration)

    bowling_rewards = get_bowling_base_rewards(row, rewards_configuration)

    fielding_rewards = get_fielding_base_rewards(row, rewards_configuration)

    return batter_rewards, non_striker_rewards, bowling_rewards, fielding_rewards


def get_bonus_penalty(row, rewards_configuration: RewardsConfiguration):
    """
    Get all the bonus and penalty values for the player specified by the row
    """
    bowling_bonus_wickets = 0.0
    bowler_bonus = 0.0
    bowler_penalty = 0.0 # TODO: To be deprecated - bowler penalties are no longer used
    batting_bonus = 0.0
    batting_penalty = 0.0 # TODO: To be deprecated - batting penalties are no longer used

    bowling_rewards = 0.0
    batting_rewards = 0.0

    match_key = row.name[0]
    inning = row.name[1]
    team = row.name[2]

    wickets_taken = row['wickets_taken']
    bowling_base_rewards = row['bowling_base_rewards']
    if pd.notna(wickets_taken) and wickets_taken > 0:
        bowling_bonus_wickets = rewards_configuration.get_bowling_rewards_for_wickets(int(wickets_taken))
        # Make sure wicket rewards are included in ER bonus / penalty calcs
        bowling_base_rewards += bowling_bonus_wickets

    player_economy_rate = row['economy_rate']
    player_deliveries = row['number_of_bowled_deliveries']
    player_total_runs = row['total_runs']

    if pd.notna(player_economy_rate):
        innings_deliveries = row['inning_number_of_bowled_deliveries']
        inning_total_runs = row['inning_total_runs']
        denominator = (innings_deliveries - player_deliveries)
        inning_economy_rate = (inning_total_runs - player_total_runs) / denominator if denominator != 0 else denominator
        # The bowling rewards are calculated by looking at the Relative ER multiplier
        bowling_rewards = rewards_configuration.get_bowling_bonus_penalty_for_economy_rate(
            player_economy_rate, inning_economy_rate, bowling_base_rewards)



    player_strike_rate = row['strike_rate']
    player_batting_runs = row['batting_total_runs']
    player_total_balls = row['total_balls']
    batting_base_rewards = row['batter_base_rewards']

    if pd.notna(player_strike_rate):
        inning_total_balls = row['inning_total_balls']
        inning_batting_runs = row['inning_batting_total_runs']
        denominator = (inning_total_balls - player_total_balls)
        inning_strike_rate = 100 * (inning_batting_runs - player_batting_runs) / denominator if denominator != 0 else 0
        # The batting rewards are calculated by looking at the Relative SR multiplier
        batting_rewards = rewards_configuration.get_batting_bonus_penalty_for_strike_rate(
            player_strike_rate, inning_strike_rate, batting_base_rewards)

    # Calculate the bonus / penalty as a result of relative rates multipliers
    bowler_bonus = bowling_rewards - bowling_base_rewards
    batting_bonus = batting_rewards - batting_base_rewards
    fielding_rewards = row['fielding_base_rewards']

    return bowling_bonus_wickets, bowler_bonus, bowler_penalty, batting_bonus, batting_penalty, \
        bowling_rewards, batting_rewards, fielding_rewards


def get_all_outcomes_by_ball_and_innnings(data_selection, is_testing, apply_labels=True):
    """
    Put together all the fields needed to calculate outcomes in one place, may also create outcome labels.
    """
    innings_df = data_selection.get_innings_for_selected_matches(is_testing)
    index_columns = ['match_key', 'inning', 'over', 'ball']
    extra_columns = ['batter_runs', 'extras', 'total_runs', 'non_boundary', 'is_wicket', 'dismissal_kind',
                     'is_direct_runout', 'byes', 'legbyes', 'noballs', 'penalty', 'wides', 'player_dismissed',
                     'bowler', 'batter', 'fielder', 'non_striker', 'batting_team', 'bowling_team']

    outcomes_df = innings_df.filter(index_columns + extra_columns, axis=1)

    if apply_labels:
        outcomes_df['bowling_outcome_index'], outcomes_df['batter_outcome_index'], \
        outcomes_df['non_striker_outcome_index'], outcomes_df['fielding_outcome_index'] \
            = zip(*innings_df.apply(lambda x: get_outcome_labels(x), axis=1))

    outcomes_df = data_selection.merge_with_players(outcomes_df, 'bowler', source_left=True)
    outcomes_df.set_index(index_columns, inplace=True, verify_integrity=True)
    outcomes_df = outcomes_df.sort_values(index_columns)

    outcomes_df.drop('name', axis=1, inplace=True)
    return outcomes_df
