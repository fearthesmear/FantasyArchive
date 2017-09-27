"""
Example URL:
 http://games.espn.com/flb/activestats?leagueId=4779&teamId=7&seasonId=2009&filter=2
 Filter parameter: 1:hitters, 2:pitchers, 3:matchup totals

"""

import collections
import pandas as pd
import numpy as np
from selenium import webdriver
from bs4 import BeautifulSoup


def get_stat_labels(soup):
    """Gets the table row of the stat names and inserts additional labels

    :param soup: BeautifulSoup object from a scrapped team year archive
    :return: list of stat labels
    """
    stat_labels = np.empty(0, dtype='object')
    stat_label_divs = soup.findAll("tr", {"class": "playerTableBgRowSubhead tableSubHead"})
    for i in range(0, len(stat_label_divs[0].contents)):
        if i != 1:
            # Index 1 causes and error when parsing because the text is a single
            # quote.
            stat_label = stat_label_divs[0].contents[i].contents[0].text
            stat_label = stat_label.replace(u'\xa0', u'')
            stat_labels = np.append(stat_labels, stat_label)
    # Insert a label for the player ID, MLB Teams, and Position
    stat_labels = np.insert(stat_labels, 1, "ID")
    stat_labels = np.insert(stat_labels, 2, "YEAR")
    stat_labels = np.insert(stat_labels, 3, "FANTASYTEAM")
    stat_labels = np.insert(stat_labels, 4, "MLBTEAM")
    stat_labels = np.insert(stat_labels, 5, "POS")
    return stat_labels

def get_hitting_individual_stats(soup):
    """Return the table of hitting stats along with the accompanying player
    info.

    :param soup:
    :return: tuple containing
        - 2D list where each row is a player and each column is the players
          extra info
        - 2D numpy array where each row is a player and each column is a stat
    """
    hitter_stats_divs = soup.findAll("tr", {"class": "pncPlayerRow"})
    hitter_stats = np.zeros([len(hitter_stats_divs),
                             len(hitter_stats_divs[0].contents) - 2])
    hitter_infos = np.empty([len(hitter_stats_divs), 4], dtype='object')

    for i in range(0, len(hitter_stats_divs)):
        name_string = hitter_stats_divs[i].contents[0].text
        pname, mteam, pos = parse_name_string(name_string)
        id = hitter_stats_divs[i].contents[0].contents[0].attrs['playerid']
        hitter_infos[i][0] = pname
        hitter_infos[i][1] = id
        hitter_infos[i][2] = mteam
        hitter_infos[i][3] = pos
        for j in range(2, len(hitter_stats_divs[i].contents)):
            stat = hitter_stats_divs[i].contents[j].text
            # Ignore ESPN using '--' for zero stats
            if stat == '--':
                stat = 0.0
            hitter_stats[i][j-2] = stat
    return (hitter_infos, hitter_stats)

def get_hitting_team_stats():
    pass

def get_pitching_stat_lables():
    pass

def get_pitching_individual_stats():
    pass

def get_pitching_team_stats():
    pass

def parse_name_string(name_string):
    """Parses a player name string into Name, position, and MLB team

    :param name_string: Name string that contains player name, MLB team, and
        positions
    :return: tuple containing the player name, the player's MLB team, and the
        players primary position.
    """
    pname_mteam_pos = name_string.split(",", 1)
    pname = pname_mteam_pos[0]
    pname = pname.replace("*", "")
    mteam_pos = pname_mteam_pos[1].lstrip(' ').split("\xa0", 1)
    mteam = mteam_pos[0]
    pos = mteam_pos[1].split(",")
    pos = pos[0]
    pos, sep, tail = pos.partition("\xa0\xa0")
    return (pname, mteam, pos)


def scrape_team_year(browser, league, year, team, stat_type):
    """Scrape the archive page for a particular team during a particular year
    and return the soup.

    :param browser: Selenium browser object
    :param league: league id number (int)
    :param year: fantasy season year (int)
    :param team: fantasy team id (int)
    :param stat_type: 1 for hitting stats, 2 for pitching stats (int)
    :return: soup object from scrapped page
    """
    team_year_url = ('http://games.espn.com/flb/activestats?leagueId='
        + str(league) + '&teamId=' + str(team) + '&seasonId=' + str(year)
        + '&filter=' + str(stat_type))
    browser.get(team_year_url)
    html_source = browser.page_source
    soup = BeautifulSoup(html_source, 'html.parser')
    return soup

def build_team_year_data_frame(browser, league, year, team, stat_type):

    soup = scrape_team_year(browser, league, year, team, stat_type)

    hit_stat_labels = get_stat_labels(soup)
    print(hit_stat_labels)

    hit_indiv_info, hit_indiv_stats = get_hitting_individual_stats(soup)
    #print(hit_indiv_info)
    np.set_printoptions(suppress=True)
    #print(hit_indiv_stats)

    # Populate dataframe with an OrderedDict
    d = collections.OrderedDict()
    team_size = hit_indiv_info.shape[0]
    d[hit_stat_labels[0]] = hit_indiv_info[:, 0]
    d[hit_stat_labels[1]] = hit_indiv_info[:, 1]
    d[hit_stat_labels[2]] = np.repeat(year, team_size, axis=0)
    d[hit_stat_labels[3]] = np.repeat(team, team_size, axis=0)
    d[hit_stat_labels[4]] = hit_indiv_info[:, 2]
    d[hit_stat_labels[5]] = hit_indiv_info[:, 3]

    # Create a dictionary from numpy label array and stats matrix
    stat_d = dict(zip(hit_stat_labels[6:], hit_indiv_stats.T))

    # Merge the dictionaries
    d.update(stat_d)

    df = pd.DataFrame(d)
    return df


if __name__ == "__main__":

    pd.set_option('display.expand_frame_repr', False)

    years = range(2007, 2017)
    league_id = 4779
    num_teams = 12

    # TODO: Headless browser with Phantom.js
    browser = webdriver.Firefox(executable_path=r'/usr/local/Cellar/geckodriver/0.18.0/bin/geckodriver')

    year_df = pd.DataFrame()
    for i in range(1, num_teams + 1):
        team_year_df = build_team_year_data_frame(browser, 4779, 2017, i, 1)
        year_df = pd.concat([year_df, team_year_df], axis=0)

    browser.quit()

    pass


