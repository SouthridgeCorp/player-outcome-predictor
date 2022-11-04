import pandas as pd


def aggregate_base_rewards(outcomes_df, team_label, player_label, base_rewards_label_source,
                           base_rewards_label_target, base_rewards_per_player_dict):
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

def get_index_columns(granularity):
    group_by_columns = ['player_key', 'tournament_key']

    if granularity == 'innings':
        group_by_columns = group_by_columns + ['stage', 'match_key', 'inning']
    elif granularity == 'match':
        group_by_columns = group_by_columns + ['stage', 'match_key']
    elif granularity == 'tournament_stage':
        group_by_columns = group_by_columns + ['stage']

    return group_by_columns