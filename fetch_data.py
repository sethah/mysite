'''
Created on May 20, 2014

@author: Seth
'''
import os, sys
#change working directory to this path
try:
    #for PA execution
    os.chdir('/home/hendris/mysite')
except:
    #for local execution
    os.chdir('C:\\Users\\Seth\\workspace\\stats_website\\src')

project_home = u'/home/hendris'
if project_home not in sys.path:
    sys.path = [project_home] + sys.path
print sys.path
from mysite import team_info_functions as tf
from mysite import game_process_functions as gpf
from datetime import datetime
from mysite import models
#from mysite import models_all_teams
from mysite import db
from mysite import link_functions as lf



def db_init():
    '''This function needs to do all the one time things that are required
    to begin a new database for a new season'''

    teamIDs = ['306']
    #make_raw_team_database()
    
    #update the new teams
    #update_raw_team_database()
    
    update_db()


    #get all the schedules for the teams
    #initialize all game objects before the season? Then fill in the data later?
    #can't figure out neutral site games until after they're played? How to get schedule that is empty from the site.
    #get_ncaa_schedule_data(teamID)
    

    #store the schedules
    #TODO: write this function

    #get all the rosters for the teams
    #tf.store_rosters(teamIDs)

def get_all_teams(year):
    link = 'http://stats.ncaa.org/team/inst_team_list?sport_code=MBB&academic_year='+str(year)+'&division=1'
    soup = lf.get_soup(link)
    table = tf.get_largest_table(soup)
    urls = table.findAll('a')
    
    teamIDs = []
    for url in urls:
        try:
            url = url['href']
            teamID = url[url.index('=')+1:len(url)]
            teamIDs.append(teamID)
        except:
            continue
    return teamIDs
def update_raw_team_database():
    #get all the teams in D1 from the NCAA website
    all_teams_new = get_all_teams(2014)
    
    #delete all teams in database
    try:
        assert False
        all_teams = models.raw_team.query.all()
        for team in all_teams:
            db.session.delete(team)
        db.session.commit()
    except:
        pass
    
    #query db for all the teams in it
    all_teams = models.raw_team.query.all()
    all_teams = [team.ncaaID for team in all_teams]

    #add the new teamID and print it
    for team in all_teams_new:
        if team not in all_teams:
            new_team = models.raw_team()
            new_team.ncaaID = team
            print 'added: '+new_team.ncaaID
            db.session.add(new_team)
    #add the new teamID and print it
    for team in all_teams:
        if team not in all_teams_new:
            delete_team = models.raw_team.query.filter(models.raw_team.ncaaID==team).first()
            db.session.delete(delete_team)
            print 'deleted: '+team
    db.session.commit()

def make_raw_team_database():
    '''This function should be called once/year to make the years new database'''
    
    #delete all teams in database
    try:
        #assert False
        all_teams = models.raw_team.query.all()
        for team in all_teams:
            db.session.delete(team)
        db.session.commit()
    except:
        pass
    
    #create the database if it doesn't exist, then query it for all the teams in it
    bind_key = 'all_teams_db'
    try:
        all_teams = models.raw_team.query.all()
        all_teams = [team.ncaaID for team in all_teams]
    except:
        db.create_all(bind=[bind_key])
        all_teams = models.raw_team.query.all()
        all_teams = [team.ncaaID for team in all_teams]

    
    #this code adds the teams from a pre-existing db
    teams = models.team.query.all()
    for team in teams:
        if team.ncaaID not in all_teams:
            new_team = models.raw_team()
            new_team.ncaaID = team.ncaaID
            new_team.ncaa = team.ncaa
            new_team.espn = team.espn
            new_team.espn_name = team.espn_name
            new_team.cbs1 = team.cbs1
            new_team.cbs2 = team.cbs2
            new_team.statsheet = team.statsheet
            db.session.add(new_team)
            print new_team.statsheet
    db.session.commit()
def update_db():
    '''This function is to be called once a day to update the games in
    the database. Does it need to handle failures of the previous day(s)
    updates? Or would that be a manual thing that could be done? Have the function
    send admin an email if the update fails.
    '''
    #use today's date
    date = datetime.today()

    #store all the raw html for games for the date in the database
    store_raw_scoreboard_games(date)

    return None

    #update the team info (rpi, sos, etc...)
    #tf.get_rpi()

    #process the data and put in db
    #query the raw database for all of the games for the date used
    raw_q = models.raw_game.query.filter(models.raw_game.date==date).all()

    for raw_game in raw_q:

        #if the team info doesn't exist for the team skip it
        home_team_obj = tf.get_team_param(raw_game.home_team, 'ncaaID')
        away_team_obj = tf.get_team_param(raw_game.away_team, 'ncaaID')

        if home_team_obj == None or away_team_obj == None:
            #TODO: add to the failed games log - this should be another table in our database
            continue

        #process the game
        #instantiate a class to hold the game info and processed rows
        pbp_game = models.game()

        pbp_game.home_team = raw_game.home_team
        pbp_game.away_team = raw_game.away_team
        pbp_game.location = raw_game.location
        pbp_game.home_outcome = raw_game.home_outcome
        pbp_game.date = raw_game.date

        box_failed = False
        pbp_failed = False
        try:
            #process the raw box score data for the game
            box_data = gpf.get_box_stat_game(raw_game.home_team,raw_game.away_team,raw_game.home_outcome,raw_game.date,raw_game.box_rows)            #store it
            for st in box_data:
                #continue
                pbp_game.box_data.append(st)

            #assign the starters for the game
            starters = []
            for plr in box_data:
                if plr.started:
                    starters.append(plr.name)
        except:
            #problem processing box data
            box_failed = True
            pass

        try:
            #process the play by play data for the game
            pbp_data = gpf.get_play_by_play(raw_game.home_team,raw_game.away_team,raw_game.date, raw_game.rows,starters)
            for st in pbp_data:
                pbp_game.pbp_data.append(st)
        except:
            #problem processing pbp data
            pbp_failed = True
            pass

        if not box_failed and not pbp_failed:
            db.session.add(pbp_game)
            db.session.flush()
            db.session.commit()
        else:
            #TODO: add to failed games
            pass

def store_raw_scoreboard_games(date):
    try:
        date_string = datetime.strftime(date,'%m/%d/%Y')
    except:
        #bad date
        return None

    #get the list of teams, box game links, and pbp links from the day's scoreboard
    teams, box_links, links = tf.get_scoreboard_games('03/13/2014')

    print teams, box_links, links
    return None

    #iterate through games
    for j in range(len(teams)):
        team1 = teams[j][0]
        team1_obj = tf.get_team_param(team1,'ncaaID')
        team2 = teams[j][1]
        team2_obj = tf.get_team_param(team2,'ncaaID')
        link = links[j]
        box_link = box_links[j]


        #if game is in database skip it
        #query for a game between the two teams on the date

        '''game_exists_q = models.raw_games.query.filter(or_(and_(models.raw_games.home_team==team1,models.raw_games.away_team==team2,models.raw_games.date==date),
                                          and_(models.raw_games.home_team==team2,models.raw_games.away_team==team1,models.raw_games.date==date))).first()
    '''
        game_exists_q = None
        #if the game was found in the database then skip this link
        if game_exists_q != None:
            continue

        store_raw_data(box_link,link,date)
def store_raw_data(box_link, pbp_link, date):
    
    #create the new raw_game instance
    this_game = models.raw_game()
    
    try:
        this_game.date = date
    except:
        #bad date
        pass
    
    #get the box_data
    box_soup = lf.get_soup(box_link)
    if box_soup != None:
        box_rows = tf.get_box_rows(box_soup)
        for row in box_rows:
            #make the raw box row to hold the soup
            raw_box_row = models.raw_box()
            raw_box_row.soup_string = str(row)
            
            #append the child row to the raw game instance
            this_game.raw_box.append(str(row))
    
    #get the pbp_data
    pbp_soup = lf.get_soup(link)
    if pbp_soup != None:
        rows = tf.get_pbp_rows(pbp_soup)
        
        for row in rows:
            #make the raw pbp row to hold the soup
            raw_pbp_row = models.raw_play
            raw_pbp_row.soup_string = str(row)
            
            #append the child row to the raw game instance
            this_game.raw_play.append(str(row))
        

        #get the home and away teams from pbp link
        home_team, away_team = tf.home_and_away_teams(pbp_soup,team1_obj.ncaa,team2_obj.ncaa)
        if home_team != None:
            this_game.home_team = home_team
            this_game.away_team = away_team
            
    db.session.commit()
    
    
#get_all_teams(2014)
db_init()