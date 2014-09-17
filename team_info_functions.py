from mysite import models
from datetime import datetime
from mysite import link_functions as lf
from mysite import data_functions as df
from mysite import db
from sqlalchemy import and_,or_
import traceback
from bs4 import BeautifulSoup

def myround(x, base=5):
    return int(base * round(float(x)/base))

def is_neutral(date, team1, team2):
    neutral = None
    for teamID in [team1,team2]:
        try:
            locations, opponents, dates = get_ncaa_schedule_data(teamID)
            idx = 0
            for d in dates:
                if d == date:
                    location = locations[idx]
                    if location == 'Neutral':
                        neutral = True
                    else:
                        neutral = False
                    break
                idx += 1
            if neutral != None:
                break
        except:
            continue

    return neutral
def get_ncaa_schedule_data(teamID):
    '''
    @Function: get_ncaa_schedule_data(teamID)
    @Author: S. Hendrickson 3/5/14
    @Return: This function returns various lists holding information
    about the team's games.
    '''

    link = 'http://stats.ncaa.org/team/index/11540?org_id='+teamID
    soup = lf.get_soup(link)
    if soup == None:
        return None

    try:
        #get the table that contains 'Schedule' in its first row
        tables = soup.findAll('table')
        tables = [table for table in tables if 'Schedule' in table.findAll('tr')[0].get_text()]
        table = tables[0]

        #get all the game rows that have been played
        rows = table.findAll('tr')

        #get all rows with more than zero cells and with a 'W' or an 'L' in the last cell
        rows = [row for row in rows if len(row.findAll('td', {'class' : 'smtext'})) > 0 and ('W' in row.findAll('td')[-1].get_text() or 'L' in row.findAll('td')[-1].get_text())]
    except:
        #assign rows empty list, will return empty lists for data
        rows = []

    dates = []
    opponents = []
    locations = []
    fmt =  '%m/%d/%Y'
    for row in rows:
        try:
            #get the date
            tds = row.findAll('td')
            date = datetime.strptime(tds[0].get_text(),fmt)
            dates.append(date.date())

            db_year = df.get_year_from_date(date)

            #get the location
            string = str(tds[1].get_text())
            string = string.strip()

            if string[0:1] == '@':
                location = 'Away'
            elif '@' in string:
                #if @ is not the first character, it is a neutral game
                location = 'Neutral'
            else:
                location = 'Home'

            #get the opponent
            try:
                opponent = tds[1].find('a')['href']
                opponent = opponent[opponent.find('=')+1:len(opponent)]

                #check to see if this team exists in the database
                q = query_by_year('team',db_year)
                opp_q = q.filter(models.team.ncaaID==opponent).first()
                if opp_q is None:
                    #opponent not in database, so use a string instead
                    assert False
            except:
                if location == 'Neutral':
                    #if it's a neutral site game then strip off the name of the venue
                    s = tds[1].get_text()
                    opponent = s[0:s.find('@')].strip()
                else:
                    opponent = tds[1].get_text().replace('@','').strip()

            #append data to the lists
            locations.append(location)
            opponents.append(opponent)
        except Exception:
            traceback.print_exc()
            #there may be some cases where it grabs a bad row, skip it
            continue

    if len(locations) == len(opponents) and len(locations) == len(dates):
        return locations, opponents, dates
    else:
        #something went wrong
        print len(locations), len(opponents), len(dates)
        print 'lists uneven in length for team %s' % teamID
        return None, None, None
def query_by_year(table_name,year,join=None):
    if type(year) != type(1):
        return None

    try:
        the_table = getattr(models,table_name)
    except:
        return None

    if table_name != 'year':
        q = the_table.query
        if join != None:
            q = q.join(getattr(models,join))
        q = q.join(models.year).filter(models.year.year==year)
    else:
        q = the_table.query
        if join != None:
            q = q.join(getattr(models,join))
        q = q.filter(models.year.year==year)
    return q
def get_team_param(the_team,convert_from):
    '''
    @Function: get_team_param(team,convert_from)
    @Author: S. Hendrickson 1/11/14
    @Return: This function indexes a lookup table and finds the
    convert_from value and returns the convert_to value in the
    found row.
    '''

    q = models.team.query.filter(getattr(models.team,convert_from)==the_team).first()
    try:
        return q
    except AttributeError:
        return None
def win_loss_invert(outcome):
    if outcome == 'W':
        return 'L'
    elif outcome == 'L':
        return 'W'
    else:
        return None

def get_scoreboard_games(date_string, the_year):
    '''
    @Function: convert_name_ncaa(name)
    @Author: S. Hendrickson 3/5/14
    @Return: This function gets the game links from stats.ncaa scoreboard html
    '''

    #construct url with the date
    scoreboard_url = 'http://stats.ncaa.org/team/schedule_list?academic_year=2014&division=1.0&sport_code=MBB&schedule_date='+date_string

    soup = lf.get_soup(scoreboard_url)

    if soup == None:
        #error getting the HTML
        msg = "couldn't get HTML"
        return None, None, None, msg

    #get the largest table on the page
    largest_table = get_largest_table(soup)

    if largest_table == None:
        #error getting table
        msg = "couldn't get largest table"
        return None, None, None, msg

    #iterate through tables in that table
    game_tables = largest_table.findAll('table')

    team_list = []
    link_list = []
    box_link_list = []
    for game in game_tables:
        #skip tables that contain tables
        if len(game.findAll('table')) != 0:
            continue

        teams = []
        box_link = None
        pbp_link = None
        try:
            rows = game.findAll('tr')
            tds = [row.findAll('td')[0] for row in rows]
            if len(tds) != 3:
                continue

            #find all the links in the game table
            game_links = game.findAll('a')

            #handle all the links
            idx = 0
            for td in tds:
                #get the url in the a tag
                try:
                    link = td.findAll('a')[0]
                    url = link['href']
                except:
                    url = ''
                    pass

                if 'team/index' in url:
                    #handle a team link
                    team_string =  link.get_text().strip()
                    teamID = url[url.index('=')+1:len(url)]
                    team_q = models.team.query.join(models.year).filter(and_(models.year.year==the_year,models.team.ncaaID==teamID)).first()
                    if team_q == None:
                        #this team isn't in the database, use the string for the team instead
                        teams.append(team_string)
                    else:
                        teams.append(teamID)
                elif url == '' and idx != 2:
                    #if there is no link for the cell, and it isn't the third cell (game score)
                    team_string =  td.get_text().strip()
                    teams.append(team_string)
                elif 'game/index' in url:
                    #handle a game link
                    index = url[url.index('/index')+len('index/')+1:url.index('?')]
                    pbp_link = 'http://stats.ncaa.org/game/play_by_play/'+index
                    box_link = 'http://stats.ncaa.org/game/box_score/'+index

                idx += 1
        except Exception, e:
            print 'bleh!'
            traceback.print_exc()
            pass

        #make sure everything is normal
        if pbp_link != None and box_link != None and len(teams) == 2:
            team_list.append(teams)
            link_list.append(pbp_link)
            box_link_list.append(box_link)

    if len(team_list) != len(link_list) or len(team_list) != len(box_link_list):
        #return none if the lists aren't equal for some reason
        msg = "lists were uneven in length"
        return None, None, None, msg

    return team_list, box_link_list, link_list, None
def home_and_away_teams(soup, team1_ncaa, team1_ncaaID, team2_ncaa, team2_ncaaID):
    '''
    This function returns a home and away team from the
    playbyplay stats page
    '''
    #look at the heading row of the play by play table
    hdr_rows = soup.findAll('tr',{'class' : 'grey_heading'})
    hdr_rows = [row for row in hdr_rows if row.findAll('td')[0].get_text().strip() == 'Time']
    tds = hdr_rows[0].findAll('td')

    #the away team is the left column
    left_col = tds[1].get_text().strip()
    right_col = tds[3].get_text().strip()
    if left_col == team1_ncaa and right_col == team2_ncaa:
        home_team = team2_ncaaID
        away_team = team1_ncaaID
    elif left_col == team2_ncaa and right_col == team1_ncaa:
        home_team = team1_ncaaID
        away_team = team2_ncaaID
    else:
        home_team = None
        away_team = None

    return home_team, away_team
def get_home_outcome(pbp_rows):
    j = 1
    while j < 10:
        try:
            this_row = pbp_rows[-j]
            try:
                bs_row = BeautifulSoup(this_row, "html.parser")
            except:
                #bad row string
                bs_row = this_row
            score_string = bs_row.findAll('td')[2].get_text()
            scores = score_string.split('-')
            if len(scores) == 2:
                away_score = int(scores[0])
                home_score = int(scores[1])
                if home_score > away_score:
                    return 'W'
                else:
                    return 'L'
            else:
                assert False
        except:
            j += 1
    return None
def get_largest_table(soup):
    '''
    @Function: get_largest_table(soup)
    @Author: S. Hendrickson 3/5/14
    @Return: This function returns the largest table in the provided
    html.
    '''
    try:
        #Get the largest table
        largest_table = None
        max_rows = 0
        for table in soup.findAll('table'):
            number_of_rows = len(table.findAll('tr'))
            if number_of_rows > max_rows:
                largest_table = table
                max_rows = number_of_rows
    except:
        return None
    return largest_table
def get_pbp_rows(soup):
    '''
    @Function: get_pbp_rows(soup)
    @Author: S. Hendrickson 5/20/14
    @Return: This function returns a list of beautifulsoup row objects that contain
    the play by play data.
    '''
    try:
        rows = soup.findAll('tr')
        rows = [str(row) for row in rows if len(row.findAll('td',{'class' : 'smtext'})) > 0]
    except:
        rows = None

    return rows
def get_box_rows(soup):
    '''
    @Function: get_box_rows(soup)
    @Author: S. Hendrickson 5/20/14
    @Return: This function returns a list of beautifulsoup row objects that contain
    the box data.
    '''
    try:
        rows = soup.findAll('tr', {'class' : 'smtext'})
        trows = soup.findAll('tr')
        trows = [str(row) for row in trows if row.findAll('td')[0].get_text().strip() == 'Totals']
        rows = [str(row) for row in rows]
        rows = rows+trows
    except:
        rows = None
    return rows
def convert_name_ncaa(name):
    '''
    @Function: convert_name_ncaa(name)
    @Author: S. Hendrickson 3/5/14
    @Return: This function returns a name, first name, and last name
    that is converted from a raw string in the format last_name, first_name.
    '''
    try:
        last_name = name[0:name.index(',')]
        first_name = name[name.index(',')+2:len(name)]
        name = first_name+' '+last_name
    except:
        last_name = None
        first_name = None
        name = None
    return name, first_name, last_name

def get_rpi(the_year):
    #TODO: this is horrendous. make the function work
    #TODO: error proof this
    '''
    @Function: get_rpi()
    @Author: S. Hendrickson 3/5/14
    @Return: This function fetches rpi and other team data and stores it in
    a lookup table.
    '''

    #try:
    #open the link and grab the HTML
    link = 'http://statsheet.com/mcb/rankings/RPI'
    soup = lf.get_soup(link)

    #get the rows of the table that has the team information
    table = get_largest_table(soup)
    rows = table.findAll('tr')
    rows = rows[1:len(rows)]
    #except:
    #    print 'asdf'
    #    rows = []

    for row in rows:
        try:
            #get the cell information defined in cats from each row
            tds = row.findAll('td')
            a = tds[1].find('a')['href']
            team = a[a.rfind('/')+1:len(a)]

            #query for the current team using statsheet attribute
            q = models.team.query.join(models.year).filter(and_(models.year.year==the_year,models.team.statsheet == team))
            the_team = q.first()

            #if the team wasn't found in the db, do nothing
            if the_team == None:
                print 'no team'
                continue

            #print the_team.statsheet
            the_team.rpi_rank = tds[0].get_text().strip()
            the_team.wins = tds[2].get_text().strip()
            the_team.losses = tds[3].get_text().strip()
            the_team.rpi = tds[4].get_text().strip()
            the_team.sos = tds[5].get_text().strip()
            the_team.sos_rank = tds[7].get_text().strip()
            the_team.conference = tds[9].get_text().strip()
            print the_team
        except:
            #error with team row
            print 'error'
            continue

    db.session.flush()
    db.session.commit()
def process_pbp_game(raw_game):

    try:
        this_game = models.game()
        this_game.date = raw_game.date
        this_game.home_team = raw_game.home_team
        this_game.away_team = raw_game.away_team
        if raw_game.location == 'Neutral':
            this_game.neutral_site = True
        else:
            this_game.neutral_site = False
        this_game.home_outcome = raw_game.home_outcome
    except:
        #problem with raw game
        return None

    #process the raw box score data for the game
    box_data = bs.get_box_stat_game(raw_game.home_team,raw_game.away_team,raw_game.home_outcome,raw_game.date,raw_game.box_rows)

    #process the play by play data for the game
    pbp_data = pbp.get_play_by_play(raw_game.home_team,raw_game.away_team,raw_game.date, raw_game.rows,starters)


    pass
def init_item(model,**kwargs):
    for key, value in kwargs.iteritems():
        setattr(model,key,value)
    return model