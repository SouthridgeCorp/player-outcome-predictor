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


def add_dataframes(df1, df2, how, columns_to_add):

    df3 = pd.merge(df1, df2, left_index=True, right_index=True, how=how)
    df3.fillna(0, inplace=True)

    for column in columns_to_add:
        df3[column] = df3[f"{column}_x"] + df3[f"{column}_y"]

    for column in df3.columns:
        if column.endswith("_x") or column.endswith("_y"):
            df3.drop(column, axis=1, inplace=True)

    return df3