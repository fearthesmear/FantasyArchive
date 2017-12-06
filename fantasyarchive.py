"""
Example URL:
 http://games.espn.com/flb/activestats?leagueId=4779&teamId=7&seasonId=2009&filter=2
 Filter parameter: 1:hitters, 2:pitchers, 3:matchup totals

"""

import sys
import argparse
import collections
import pandas as pd
import numpy as np
import time
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from bs4 import BeautifulSoup

# TODO: Headless browser. Maybe Phantom.js
# TODO: Figure out how many owners instead of asking for it, since it my vary year to year.
# TODO: Associate owner names?/team names? with fantasy team ID and carry in dataframe
# TODO: Allow for manual mapping for owners/teams to player IDs.
# TODO: Handle 2007 and before H/AB by breaking into H and AB.

def get_stat_labels(soup):
    """Gets the table row of the stat names and inserts additional labels

    :param soup: BeautifulSoup object from a scrapped team year archive
    :return: list of stat labels
    """
    stat_labels = np.empty(0, dtype='object')
    stat_label_divs = soup.findAll("tr", {"class": "playerTableBgRowSubhead tableSubHead"})
    for i in range(2, len(stat_label_divs[0].contents)):
        stat_label = stat_label_divs[0].contents[i].contents[0].text
        stat_label = stat_label.replace(u'\xa0', u'')
        stat_labels = np.append(stat_labels, stat_label)
    # Insert a label for the player ID, MLB Teams, and Position
    stat_labels = np.insert(stat_labels, 0, "PLAYER")
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
        #id = stats_divs[i].contents[0].contents[0].attrs['playerid']
        id = stats_divs[i].attrs['id']
        id = id.replace("plyr", "")
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


def login(driver, username, password):
    """ Log into ESPN
    :param driver: Selenium webdriver instance
    :param username: ESPN username
    :param password: ESPN Password
    """
    # initialize variables
    driver.get("http://games.espn.go.com/flb/signin")
    wait = WebDriverWait(driver, 10)

    # click Log In button
    loginButtonXpath = "//*[@id='global-header']/div[2]/ul/li[2]/a"
    loginButtonElement1 = wait.until(
        lambda driver: driver.find_element_by_xpath(loginButtonXpath))
    loginButtonElement1.click()

    # find email and pass ID
    emailFieldID = "//*[@id='did-ui']/div/div/section/section/form/section/div[1]/div/label/span[2]/input"
    passFieldID = "//*[@id='did-ui']/div/div/section/section/form/section/div[2]/div/label/span[2]/input"

    # switch to frame so script can type
    driver.switch_to.frame("disneyid-iframe")

    # find email input box and type in email
    emailFieldElement = wait.until(
        lambda driver: driver.find_element_by_xpath(emailFieldID))
    emailFieldElement.click()
    emailFieldElement.clear()
    emailFieldElement.send_keys(username)

    # find pass input box and type in password
    passFieldElement = wait.until(
        lambda driver: driver.find_element_by_xpath(passFieldID))
    passFieldElement.click()
    passFieldElement.clear()
    passFieldElement.send_keys(password)

    time.sleep(1.0)
    # click log in button
    loginButtonXpath2 = "//*[@id='did-ui']/div/div/section/section/form/section/div[3]/button[2]"
    loginButtonElement2 = wait.until(
        lambda driver: driver.find_element_by_xpath(loginButtonXpath2))
    loginButtonElement2.click()

    time.sleep(3.0)

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='ESPN Fantasy Baseball '
                                     'web scrapper that produces CSVs')
    parser.add_argument('league_id',
                        help='ESPN Fantasy Baseball League ID number')
    parser.add_argument('startyear',
                        help='Earliest year to include.')
    parser.add_argument('stopyear',
                        help='Latest year to include.')
    parser.add_argument('-u', '--username', required=True,
                        help='ESPN username.')
    parser.add_argument('-p', '--password', required=True,
                        help='ESPN password.')
    args = parser.parse_args()

    pd.set_option('display.expand_frame_repr', False)

    # Input parsing
    if args.startyear > args.stopyear:
        sys.exit("Input argument startyear cannot be large than stopyear. Exiting.")
    years = np.arange(int(args.startyear),int(args.stopyear)+1)
    league_id = args.league_id
    num_teams = 12

    # Create a browser and login to ESPN
    browser = webdriver.Firefox(executable_path=r'/usr/local/Cellar/geckodriver/0.18.0/bin/geckodriver')
    login(browser, args.username, args.password)

    # Build hitting and pitching data frames that include each year and team's
    # active stats.
    hit_indiv_df = pd.DataFrame()
    pitch_indiv_df = pd.DataFrame()
    for i in np.nditer(years):
        for j in range(1, num_teams + 1):
            # Hitting for the team and year
            hit_team_year_df = build_indiv_team_year_data_frame(browser, 4779, i, j, 1)
            hit_indiv_df = pd.concat([hit_indiv_df, hit_team_year_df], axis=0)
            # Pitching for the team and year
            pitch_team_year_df = build_indiv_team_year_data_frame(browser, 4779, i, j, 2)
            pitch_indiv_df = pd.concat([pitch_indiv_df, pitch_team_year_df], axis=0)
            print('Completed year {} for team {}'.format(i, j))

    browser.quit()

    hit_indiv_df.to_csv('hit_indiv.csv', sep=',', encoding='utf-8')
    pitch_indiv_df.to_csv('pitch_indiv.csv', sep=',', encoding='utf-8')

    pass


