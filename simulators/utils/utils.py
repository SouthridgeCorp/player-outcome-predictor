import pandas as pd


def aggregate_base_rewards(outcomes_df, team_label, player_label, base_rewards_label_source,
                           base_rewards_label_target, base_rewards_per_player_dict):
    """
    Calculate base_rewards at a team_label & player_label level, and then save them into a player level data structure
    so that all rewards (bowling, fielding, batting, non-striker) for a player for a match & innings are available in
    the same row in a dataframe.
    """
    for g, g_df in outcomes_df.groupby(['match_key', 'inning', team_label, player_label]):
        total_rewards = g_df[base_rewards_label_source].sum()
        if g in base_rewards_per_player_dict.keys():
            player_dict = base_rewards_per_player_dict[g]
        else:
            player_dict = {'match_key': g[0], 'inning': g[1], 'team': g[2], 'player_key': g[3]}
            base_rewards_per_player_dict[g] = player_dict
        if base_rewards_label_target in player_dict.keys():
            total_rewards += player_dict[base_rewards_label_target]

        player_dict[base_rewards_label_target] = total_rewards

def aggregate_base_rewards_df(outcomes_df, team_label, player_label, base_rewards_label_source,
                              base_rewards_label_target):
    grouping = outcomes_df.groupby(['match_key', 'inning', team_label, player_label])
    aggregate_df = pd.DataFrame()
    aggregate_df[base_rewards_label_target] = grouping[base_rewards_label_source].sum()
    aggregate_df = aggregate_df.reset_index()
    aggregate_df.rename(columns={player_label: 'player_key', team_label: 'team'}, inplace=True)
    aggregate_df.set_index(['match_key', 'inning', 'team', 'player_key'], inplace=True, verify_integrity=True)

    return aggregate_df
