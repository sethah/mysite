'''
Created on May 20, 2014

@author: Seth
'''
import os, sys
dir = 'C:\\Users\\Seth\\workspace\\stats2\\src\\mysite'
if dir not in sys.path:
    sys.path.insert(0,dir)
from mysite import team_info_functions as tf
from mysite import game_process_functions as gpf
from datetime import datetime
from mysite import models
from mysite import db
from mysite import link_functions as lf

def db_init():
    '''This function needs to do all the one time things that are required
    to begin a new database for a new season'''
    
    #check to see if there are new D1 teams and add them to the database
        #get all the ncaa teams from the teams page on the website
        #TODO: write this function
        #query the team sql lite db to see if any aren't there
        #TODO: This will require configuring multiple databases
        #TODO: make this database
        #TODO: use a different team model with only static team information, also
        #create this team database new for every year
        #manually add them to the db by collecting their statsheet and ESPN info
    
    #get all the schedules for the teams
    #get_ncaa_schedule_data(teamID)
    
    #store the schedules
    #TODO: write this function
    
    #get all the rosters for the teams
    #tf.store_rosters(teamIDs)
    


def update_db():
    '''This function is to be called once a day to update the games in
    the database. Does it need to handle failures of the previous day(s)
    updates? Or would that be a manual thing that could be done? Have the function
    send admin an email if the update fails.
    '''
    #use today's date
    date = datetime.today()
    
    #store all the raw html for games for the date in the database
    get_scoreboard_games(date)
    
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

def get_scoreboard_games(date):
    try:
        date_string = datetime.strftime(date,'%m/%d/%Y')
    except:
        #bad date
        return None
    
    #get the list of teams, box game links, and pbp links   
    teams, box_links, links = tf.get_scoreboard_games('03/13/2014')
    
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
             
        #create raw_game instance
        this_game = models.raw_game()
            
        #get the box_data
        box_soup = lf.get_soup(box_link)
        if box_soup != None:
            this_game.box_rows = tf.get_box_rows(box_soup)
        else:
            this_game.box_rows = None
            
        #get the pbp_data
        pbp_soup = lf.get_soup(link)
        if pbp_soup != None:
            this_game.rows = tf.get_pbp_rows(pbp_soup)
            
            if team1_obj != None and team2_obj != None:
                #get the home and away teams from pbp link
                home_team, away_team = tf.home_and_away_teams(pbp_soup,team1_obj.ncaa,team2_obj.ncaa)
                if home_team != None:
                    this_game.home_team = home_team
                    this_game.away_team = away_team
        else:
            this_game.rows = None
        
        #assign the date as the date of the scoreboard url
        this_game.date = date
        
        print len(this_game.rows),len(this_game.box_rows)
        
        #TODO: put in database

