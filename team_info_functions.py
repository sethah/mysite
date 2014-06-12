from mysite import models
from datetime import datetime
from flask import flash
from mysite import link_functions as lf
from mysite import db

def myround(x, base=5):
    return int(base * round(float(x)/base))

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
def get_ncaa_schedule_data(teamID):
    '''
    @Function: get_ncaa_schedule_data(teamID)
    @Author: S. Hendrickson 3/5/14
    @Return: This function returns various lists holding information
    about the team's games.
    '''
    link = 'http://stats.ncaa.org/team/index/11540?org_id='+teamID
    soup = lf.get_soup(link)

    #get the table that contains 'Schedule' in its first row
    tables = soup.findAll('table')
    tables = [table for table in tables if 'Schedule' in table.findAll('tr')[0].get_text()]
    table = tables[0]

    #get all the game rows that have been played
    rows = table.findAll('tr')

    #get all rows with more than zero cells and with a 'W' or an 'L' in the last cell
    rows = [row for row in rows if len(row.findAll('td', {'class' : 'smtext'})) > 0 and ('W' in row.findAll('td')[-1].get_text() or 'L' in row.findAll('td')[-1].get_text())]

    dates = []
    outcomes = []
    opponents = []
    locations = []
    links = []
    games = []
    real_locations = []
    box_links = []
    fmt =  '%m/%d/%Y'
    for row in rows:
        #get the date
        tds = row.findAll('td')
        date = datetime.datetime.strptime(tds[0].get_text(),fmt)
        dates.append(date)

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
        opponent = tds[1].find('a')['href']
        opponent = opponent[opponent.find('=')+1:len(opponent)]

        #get the data from the souped table
        string = tds[-1].get_text().strip()
        outcome = str(string[0:1].upper())
        link = tds[-1].find('a')['href']
        index = link[link.index('index/')+len('index/'):link.index('?')]
        link = 'http://stats.ncaa.org/game/play_by_play/'+index
        box_link = 'http://stats.ncaa.org/game/box_score/'+index

        #append data to the lists
        box_links.append(box_link)
        links.append(link)
        outcomes.append(outcome)
        locations.append(location)
        opponents.append(opponent)
        games.append([teamID,opponent,date])

    #real locations no longer returned
    return links, box_links, outcomes, locations, real_locations, opponents, dates, games
def get_scoreboard_games(date_string):
    '''
    @Function: convert_name_ncaa(name)
    @Author: S. Hendrickson 3/5/14
    @Return: This function gets the game links from stats.ncaa scoreboard html
    '''
    
    #construct url with the date
    scoreboard_url = 'http://stats.ncaa.org/team/schedule_list?academic_year=2014&division=1.0&sport_code=MBB&schedule_date='+date_string
    
    soup = lf.get_soup(scoreboard_url)
    
    #get the largest table on the page
    largest_table = get_largest_table(soup)
    
    #iterate through tables in that table
    game_tables = largest_table.findAll('table')
    
    team_list = []
    link_list = []
    box_link_list = []
    for game in game_tables:
        #skip the larger table containers
        if len(game.findAll('table')) != 0:
            continue
        
        teams = []
        box_link = None
        pbp_link = None
        try:
            #find all the links in the game table
            game_links = game.findAll('a')
            
            #handle all the links
            for link in game_links:
                #get the url in the a tag
                try:
                    url = link['href']
                except:
                    continue
                
                if 'team/index' in url:
                    #handle a team link
                    teams.append(url[url.index('=')+1:len(url)])
                elif 'game/index' in url:
                    #handle a game link
                    index = url[url.index('/index')+len('index/')+1:url.index('?')]
                    pbp_link = 'http://stats.ncaa.org/game/play_by_play/'+index
                    box_link = 'http://stats.ncaa.org/game/box_score/'+index
        except:
            pass
        
        #make sure everything is normal
        if pbp_link != None and box_link != None and len(teams) == 2:
            team_list.append(teams)
            link_list.append(pbp_link)
            box_link_list.append(box_link)
    
    if len(team_list) != len(link_list) or len(team_list) != len(box_link_list):
        #return none if the lists aren't equal for some reason
        team_list = None
        box_link_list = None
        link_list = None
    
    return team_list, box_link_list, link_list
def home_and_away_teams(soup,team1,team2):
    '''
    @Function: home_and_away_teams(soup,team1,team2)
    @Author: S. Hendrickson 5/20/14
    @Return: This function returns a home and away team from the 
    playbyplay stats page
    '''
    #look at the heading row of the play by play table
    hdr_rows = soup.findAll('tr',{'class' : 'grey_heading'})
    hdr_rows = [row for row in hdr_rows if row.findAll('td')[0].get_text().strip() == 'Time']
    tds = hdr_rows[0].findAll('td')
    
    #the away team is the left column
    if tds[1].get_text().strip() == team1 and tds[2].get_text().strip() == team2:
        home_team = team1
        away_team = team2
    elif tds[1].get_text().strip() == team2 and tds[2].get_text().strip() == team1:
        home_team = team2
        away_team = team1
    else:
        home_team = None
        away_team = None
    return home_team, away_team
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
def get_roster(teamID):
    '''
    @Function: get_roster(teamID)
    @Author: S. Hendrickson 3/5/14
    @Return: This function returns lists holding roster 
    information for a given team. 
    '''
    link = 'http://stats.ncaa.org/team/roster/11540?org_id='+teamID
    soup = lf.get_soup(link)
    if soup == None:
        return None
    try:
        body = soup.find('tbody')
        rows = body.findAll('tr')
    except:
        #error in html
        rows = []

    first_names = []
    last_names = []
    heights = []
    positions = []
    pclasses = []
    names = []
    for row in rows:
        tds = row.findAll('td')
        if len(tds) > 6:
            #TODO: does strip fail if get_text returns None?
            name = tds[1].get_text().strip()
            position = tds[2].get_text().strip()
            height = tds[3].get_text().strip()
            pclass = tds[4].get_text().strip()
            
            try:
                feet = height[0:height.find('-')]
                inches = height[height.find('-')+1:len(height)]
                height = int(feet)*12+int(inches)
            except:
                #error with height data
                height = 0
            
            positions.append(position)
            heights.append(height)
            pclasses.append(pclass)
            name, first_name, last_name = convert_name_ncaa(name)
            first_names.append(first_name)
            last_names.append(last_name)
            names.append(first_name+' '+last_name)
    return first_names, last_names, names, positions, heights, pclasses
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
def store_rosters(teamIDs):
    '''
    @Function: store_rosters(teamIDs)
    @Author: S. Hendrickson 3/5/14
    @Return: This function stores a team's roster and other various info and 
    stores it in a database
    '''
    #TODO: error handling
    
    for teamID in teamIDs:
        #get the team
        the_team, exists = sdb.get_or_create(sess.session,c.team,None, ncaaID = teamID)
        if not exists:
            #TODO: add the team
            continue
        print the_team.statsheet
        
        #query for all players that belong to this team
        q = models.player.query.join(models.team).filter(models.team.ncaaID==teamID).all()

        #delete the players that exist
        for plr in q:
            print plr.name
            db.session.delete(plr)

        #call function to get the information
        first_names, last_names, names, positions, heights, pclasses = get_roster(teamID)
        
        #add the players fetched from the website
        for j in range(len(first_names)):
            plr = models.player()
            plr = sdb.init_item(plr,first_name = first_names[j],last_name = last_names[j], name = names[j], position = positions[j],
                                height = heights[j], pclass = pclasses[j])
            the_team.players.append(plr)
        
        db.session.add(the_team)
        db.session.flush()
        #sess.session.rollback()
        db.session.commit()
        
def get_ncaa_schedule_data(teamID):
    '''
    @Function: get_ncaa_schedule_data(teamID)
    @Author: S. Hendrickson 3/5/14
    @Return: This function returns various lists holding information 
    about the team's games. 
    '''
    #TODO: error handling
    
    link = 'http://stats.ncaa.org/team/index/11540?org_id='+teamID
    po = c.Page_Opener()
    soup = po.open_and_soup(link)

    #get the table that contains 'Schedule' in its first row
    tables = soup.findAll('table')
    tables = [table for table in tables if 'Schedule' in table.findAll('tr')[0].get_text()]
    table = tables[0]
    
    #get all the game rows that have been played
    rows = table.findAll('tr')
    
    #get all rows with more than zero cells and with a 'W' or an 'L' in the last cell
    rows = [row for row in rows if len(row.findAll('td', {'class' : 'smtext'})) > 0 and ('W' in row.findAll('td')[-1].get_text() or 'L' in row.findAll('td')[-1].get_text())]
    
    dates = []
    outcomes = []
    opponents = []
    locations = []
    links = []
    games = []
    real_locations = []
    box_links = []
    fmt =  '%m/%d/%Y'
    for row in rows:
        #get the date
        tds = row.findAll('td')
        date = datetime.datetime.strptime(tds[0].get_text(),fmt)
        dates.append(date)
        
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
        opponent = tds[1].find('a')['href']
        opponent = opponent[opponent.find('=')+1:len(opponent)]
        
        #get the data from the souped table
        string = tds[-1].get_text().strip()
        outcome = str(string[0:1].upper()) 
        link = tds[-1].find('a')['href']
        index = link[link.index('index/')+len('index/'):link.index('?')]
        link = 'http://stats.ncaa.org/game/play_by_play/'+index
        box_link = 'http://stats.ncaa.org/game/box_score/'+index
        
        #append data to the lists
        box_links.append(box_link)
        links.append(link)
        outcomes.append(outcome)
        locations.append(location)
        opponents.append(opponent)
        games.append([teamID,opponent,date])
        
    #real locations no longer returned
    return links, box_links, outcomes, locations, opponents, dates, games
def get_rpi():
    #TODO: this is horrendous. make the function work
    '''
    @Function: get_rpi(hdrs)
    @Author: S. Hendrickson 3/5/14
    @Return: This function fetches rpi and other team data and stores it in
    a lookup table.
    '''
    #open the link and grab the HTML
    link = 'http://statsheet.com/mcb/rankings/RPI'
    po = models.Page_Opener()
    soup = po.open_and_soup(link)
    
    #get the rows of the table that has the team information
    table = get_largest_table(soup)
    rows = table.findAll('tr')
    rows = rows[1:len(rows)]
    
    for row in rows:
        #get the cell information defined in cats from each row
        tds = row.findAll('td')
        a = tds[1].find('a')['href']
        team = a[a.rfind('/')+1:len(a)]
        
        #query for the current team using statsheet attribute
        q = models.team.query.filter(models.team.statsheet == team)
        the_team = q.first()
        
        
        #if the team wasn't found in the db, do nothing
        if the_team == None:
            #print 'nothing'
            continue

        #print the_team.statsheet
        the_team.rpi_rank = tds[0].get_text().strip()
        the_team.wins = tds[2].get_text().strip()
        the_team.losses = tds[3].get_text().strip()
        the_team.rpi = tds[4].get_text().strip()
        the_team.sos = tds[5].get_text().strip()
        the_team.sos_rank = tds[7].get_text().strip()
        the_team.conference = tds[9].get_text().strip()
        
    sess.session.flush()
    #sess.session.rollback
    sess.session.commit()
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