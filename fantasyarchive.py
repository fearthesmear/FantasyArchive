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

def get_individual_stats(soup):
    """Return the table of individual stats along with the accompanying player
    info.

    :param soup:
    :return: tuple containing
        - 2D list where each row is a player and each column is the players
          extra info
        - 2D numpy array where each row is a player and each column is a stat
    """
    stats_divs = soup.findAll("tr", {"class": "pncPlayerRow"})
    stats = np.zeros([len(stats_divs),
                             len(stats_divs[0].contents) - 2])
    infos = np.empty([len(stats_divs), 4], dtype='object')

    for i in range(0, len(stats_divs)):
        name_string = stats_divs[i].contents[0].text
        pname, mteam, pos = parse_name_string(name_string)
        id = stats_divs[i].contents[0].contents[0].attrs['playerid']
        infos[i][0] = pname
        infos[i][1] = id
        infos[i][2] = mteam
        infos[i][3] = pos
        for j in range(2, len(stats_divs[i].contents)):
            stat = stats_divs[i].contents[j].text
            # Ignore ESPN using '--' for zero stats
            if stat == '--':
                stat = 0.0
            stats[i][j-2] = stat
    return (infos, stats)

def get_team_stats():
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

def build_indiv_team_year_data_frame(browser, league, year, team, stat_type):
    """Build a Pandas DataFrame for the team's individual  hitting or pitching
    fantasy year.

    :param browser: Selenium browser object
    :param league: league id number (int)
    :param year: fantasy season year (int)
    :param team: fantasy team id (int)
    :param stat_type: 1 for hitting stats, 2 for pitching stats (int)
    :return: Pandas DataFrame for with the teams hitting or pitching yearly
             stats
    """

    soup = scrape_team_year(browser, league, year, team, stat_type)

    stat_labels = get_stat_labels(soup)

    indiv_info, indiv_stats = get_individual_stats(soup)

    np.set_printoptions(suppress=True)

    # Populate dataframe with an OrderedDict
    d = collections.OrderedDict()
    team_size = indiv_info.shape[0]
    d[stat_labels[0]] = indiv_info[:, 0]
    d[stat_labels[1]] = indiv_info[:, 1]
    d[stat_labels[2]] = np.repeat(year, team_size, axis=0)
    d[stat_labels[3]] = np.repeat(team, team_size, axis=0)
    d[stat_labels[4]] = indiv_info[:, 2]
    d[stat_labels[5]] = indiv_info[:, 3]

    # Create a dictionary from numpy label array and stats matrix
    stat_d = dict(zip(stat_labels[6:], indiv_stats.T))

    # Merge the dictionaries
    d.update(stat_d)

    df = pd.DataFrame(d)
    return df


if __name__ == "__main__":

    pd.set_option('display.expand_frame_repr', False)

    years = range(2007, 2017)
    league_id = 4779
    num_teams = 1

    # TODO: Headless browser with Phantom.js
    browser = webdriver.Firefox(executable_path=r'/usr/local/Cellar/geckodriver/0.18.0/bin/geckodriver')

    hit_year_df = pd.DataFrame()
    pitch_year_df = pd.DataFrame()
    for i in range(1, num_teams + 1):
        # Hitting for the team and year
        hit_team_year_df = build_indiv_team_year_data_frame(browser, 4779, 2017, i, 1)
        hit_year_df = pd.concat([hit_year_df, hit_team_year_df], axis=0)
        # Pitching for the team and year
        pitch_team_year_df = build_indiv_team_year_data_frame(browser, 4779, 2017, i, 1)
        pitch_year_df = pd.concat([pitch_year_df, pitch_team_year_df], axis=0)

    browser.quit()

    pass


