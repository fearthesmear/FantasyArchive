"""
Example URL:
 http://games.espn.com/flb/activestats?leagueId=4779&teamId=7&seasonId=2009&filter=2
 Filter parameter: 1:hitters, 2:pitchers, 3:matchup totals

"""

import pandas
import numpy as np
from selenium import webdriver
from bs4 import BeautifulSoup

# Gets the table row of the stat names
def get_hitting_stat_labels():
    stat_labels = []
    stat_label_divs = soup.findAll("tr", {"class": "playerTableBgRowSubhead tableSubHead"})
    for i in range(0, len(stat_label_divs[0].contents)):
        if i != 1:
            # Index 1 causes and error when parsing because the text is a single
            # quote.
            stat_label = stat_label_divs[0].contents[i].contents[0].text
            stat_label = stat_label.replace(u'\xa0', u'')
            stat_labels.append(stat_label)
    return stat_labels

def get_hitting_individual_stats():
    # TODO: If there is a star at the end of a name remove it.
    hitter_stats_divs = soup.findAll("tr", {"class": "pncPlayerRow"})
    hitter_stats = np.zeros([len(hitter_stats_divs),
                             len(hitter_stats_divs[0].contents) - 1])
    for i in range(0, len(hitter_stats_divs)):
        name = hitter_stats_divs[i].contents[0].text
        print(name)
        for j in range(2, len(hitter_stats_divs[i].contents)):
            hitter_stats[i][j-2] = hitter_stats_divs[i].contents[j].text
    pass

def get_hitting_team_stats():
    pass

def get_pitching_stat_lables():
    pass

def get_pitching_individual_stats():
    pass

def get_pitching_team_stats():
    pass


if __name__ == "__main__":
    browser = webdriver.Firefox(executable_path=r'/usr/local/Cellar/geckodriver/0.18.0/bin/geckodriver')
    browser.get('http://games.espn.com/flb/activestats?leagueId=4779&teamId=7&filter=1')
    html_source = browser.page_source
    browser.quit()
    soup = BeautifulSoup(html_source, 'html.parser')

    stat_labels = get_hitting_stat_labels()
    hitter_team_stats = get_hitting_individual_stats()
    print(stat_labels)
    pass


