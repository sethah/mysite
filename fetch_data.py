'''
Created on May 20, 2014

@author: Seth
'''
import os, sys
dir = 'C:\\Users\\Seth\\workspace\\stats2\\src\\mysite'
if dir not in sys.path:
    sys.path.insert(0,dir)
from mysite import team_info_functions as tf
from datetime import datetime
from mysite import models
from mysite import link_functions as lf
date = datetime.today()
date_string = datetime.strftime(date,'%m/%d/%Y')
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
    
    #put in database

