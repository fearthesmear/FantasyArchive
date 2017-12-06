import pandas as pd
import argparse
import numpy as np
import seaborn as sea



def hit_counting_stat_leader_by_team(hit_df, stat, team_id, team_name, n):
    """
    Return each team's hitter with the most ABs

    :return:
    """
    this_team = hit_df[(hit_df.FANTASYTEAM == team_id)]
    #Group by player ID and return sum of their ABs
    teams_total_abs_per_player = this_team.groupby(['ID'], as_index=False)[stat].sum()
    # Sort by ABs
    sorted_total_abs_per_player = teams_total_abs_per_player.sort_values([stat], ascending=False).reset_index(drop=True)
    # Select the top 5 for the team
    top_ids = sorted_total_abs_per_player[0:n]['ID']._values
    top_stats = sorted_total_abs_per_player[0:n][stat]._values
    top_players = []
    top_teamid = [team_id] * n
    top_teamname = [team_name] * n
    for id in top_ids:
        player = this_team.ix[(this_team.ID == id), 'PLAYER'].values[0]
        top_players.append(player)
    stat_leaders = pd.DataFrame({'TEAM': top_teamname,
                               'PLAYER': top_players,
                                stat: top_stats})
    stat_leaders = stat_leaders[['TEAM', 'PLAYER', stat]]
    return stat_leaders

    #sorted_total_abs_per_player.to_csv('hit_check.csv', sep=',', encoding='utf-8')

def load():
    hit_df = pd.read_csv("/Users/msmearcheck/code/FantasyArchive/hit_indiv.csv")
    return hit_df

if __name__ == "__main__":
    np.set_printoptions(suppress=True)

    hit_df = load()
    print("Loaded hitting")

    team_ab_leaders = hit_counting_stat_leader_by_team(hit_df, 'R', 7, 'Evil Empire', 10)
    print(team_ab_leaders)