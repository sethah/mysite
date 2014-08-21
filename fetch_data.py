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

from sqlalchemy import and_, or_
from mysite import team_info_functions as tf
from mysite import game_process_functions as gpf
from mysite import data_functions as df
from datetime import datetime
from mysite import models
from mysite import db
from mysite import link_functions as lf
import smtplib, traceback

current_year = df.get_year()

#global year constant
db_year = 2014

def main():
    '''This function needs to do all the one time things that are required
    to begin a new database for a new season'''

    '''q = models.game.query.join(models.year).filter(and_(models.year.year==current_year,models.game.home_team=='17', models.game.away_team=='Tougaloo')).all()
    print len(q)
    print q[0]
    return None'''

    #use today's date
    the_date = datetime.today().date()

    date_string = '11/10/2013'
    the_date = datetime.strptime(date_string,'%m/%d/%Y').date()
    #df.get_year_from_date(the_date)
    #return None
    #tf.get_scoreboard_games(date_string, current_year)
    #return None

    update_db(the_date)
    return None
    q = models.pbp_stat.query.join(models.game).join(models.year).filter(models.year.year==2014).all()
    print len(q)


def update_db(the_date):
    '''This function is to be called once a day to update the games in
    the database. Does it need to handle failures of the previous day(s)
    updates? Or would that be a manual thing that could be done? Have the function
    send admin an email if the update fails.
    '''
    try:
        date_string = datetime.strftime(the_date,'%m/%d/%Y')
    except:
        return None

    update_teams = []

    #store all the raw html for games for the date in the database
    store_raw_scoreboard_games_errors = store_raw_scoreboard_games(the_date,update_teams)
    #return None
    if len(store_raw_scoreboard_games_errors) > 0:
        #call function to email the error list
        send_errors('raw game errors '+date_string,store_raw_scoreboard_games_errors)
        for e in store_raw_scoreboard_games_errors:
            print e
        pass
        return None

    #update the team info (rpi, sos, etc...)
    #tf.get_rpi()

    #process the day's raw games into data
    pbp_errors = process_raw_games(the_date,update_teams)
    if len(pbp_errors) != 0:
        #call function to email the error list
        send_errors('pbp errors '+date_string,pbp_errors)
        for e in pbp_errors:
            print e
        pass
def process_raw_games(the_date,update_teams = []):
    errors = []

    try:
        date_string = datetime.strftime(the_date,'%m/%d/%Y')
    except:
        errors.append('bad date')
        return errors

    #query the raw database for all of the games for the date used
    raw_q = models.raw_game.query.join(models.year).filter(and_(models.year.year==current_year,models.raw_game.date==the_date)).all()

    if raw_q == None:
        errors.append('No raw games found for this date, %s' % date_string)
        return errors

    #query for the year object to add the games to
    the_year =  models.year.query.filter(models.year.year==current_year).first()

    if the_year == None:
        errors.append('No year found for pbp processing')
        return errors

    for raw_game in raw_q:
        game_year = df.get_year_from_date(raw_game.date)

        if update_teams != []:
            if raw_game.home_team not in update_teams and raw_game.away_team not in update_teams:
                #print raw_game.home_team, raw_game.away_team
                continue
        try:
            #see if the pbp game already exists
            this_game = models.game.query.filter(or_(and_(models.game.date==the_date,models.game.home_team==raw_game.home_team,models.game.away_team==raw_game.away_team),
                                                and_(models.game.date==the_date,models.game.away_team==raw_game.home_team,models.game.home_team==raw_game.away_team))).first()

            #if both teams don't exist in the database, then assign a win/loss and continue
            home_team_obj = models.team.query.join(models.year).filter(and_(models.year.year==game_year,models.team.ncaaID==raw_game.home_team)).first()
            away_team_obj = models.team.query.join(models.year).filter(and_(models.year.year==game_year,models.team.ncaaID==raw_game.away_team)).first()
            print raw_game.home_team, raw_game.away_team, game_year, raw_game.date

            if this_game != None:
                #the game exists
                '''print raw_game.home_team, raw_game.away_team
                continue'''
                if this_game.neutral_site:
                    #if it's a neutral site game, then update the home and away teams
                    this_game.home_team = raw_game.home_team
                    this_game.away_team = raw_game.away_team
                pbp_game = this_game

                #delete any box stats or pbp stats from the game
                pbp_game.box_stats.delete()
                pbp_game.pbp_stats.delete()
                db.session.flush()
            else:
                print 'game no exist'
                #the game doesn't exist
                pbp_game = models.game()
                pbp_game.home_team = raw_game.home_team
                pbp_game.away_team = raw_game.away_team
                pbp_game.home_outcome = raw_game.home_outcome
                pbp_game.date = raw_game.date
                #TODO

                #check if it is a neutral site game
                    #check the team's schedule page for this date

            if home_team_obj == None or away_team_obj == None:
                pbp_rows = raw_game.raw_pbp_stats.all()
                pbp_rows = [pbp_row.soup_string for pbp_row in pbp_rows]
                pbp_data = gpf.get_play_by_play(raw_game.home_team,raw_game.away_team,raw_game.date, pbp_rows,[])

                #assign some score attributes to the game
                pbp_game.home_outcome = gpf.get_home_outcome(pbp_data)
                pbp_game.home_score = int(pbp_data[-1].home_score)
                pbp_game.away_score = int(pbp_data[-1].away_score)
                print pbp_game
                db.session.flush()
                db.session.commit()
                print 'no stats'
                continue
        except Exception, e:
            traceback.print_exc()
            #error instantiating new pbp game
            errors.append('failed to instantiate new game for: %s, %s, %s' % (raw_game.home_team, raw_game.away_team, date_string))
            continue


        try:
            #process the raw box score data for the game
            box_rows = models.raw_box.query.join(models.raw_game).filter(and_(models.raw_game.home_team==raw_game.home_team,models.raw_game.away_team==raw_game.away_team,models.raw_game.date==raw_game.date)).all()
            if box_rows == None:
                #TODO: should I do something different here, to just say that there weren't any raw data rows?
                assert False
            box_rows = [box_row.soup_string for box_row in box_rows]

            box_data = gpf.get_box_stat_game(raw_game.home_team,raw_game.away_team,raw_game.home_outcome,raw_game.date,box_rows)            #store it
            for st in box_data:
                #continue
                pbp_game.box_stats.append(st)

            #assign the starters for the game
            starters = []
            for plr in box_data:
                if plr.started:
                    starters.append(plr.name)
            print 'box stats successful'
        except Exception, e:
            traceback.print_exc()
            #problem processing box data
            box_error_msg = "box stats failed: %s, %s, %s" % (date_string, raw_game.home_team, raw_game.away_team)
            db.session.rollback()
            errors.append(box_error_msg)
            continue

        try:
            pbp_rows = models.raw_play.query.join(models.raw_game).filter(and_(models.raw_game.home_team==raw_game.home_team,models.raw_game.away_team==raw_game.away_team,models.raw_game.date==raw_game.date)).all()
            if pbp_rows == None:
                #TODO: should I do something different here, to just say that there weren't any raw data rows?
                assert False
            pbp_rows = [pbp_row.soup_string for pbp_row in pbp_rows]
            #process the play by play data for the game
            pbp_data = gpf.get_play_by_play(raw_game.home_team,raw_game.away_team,raw_game.date, pbp_rows,starters)

            #assign some score attributes to the game
            pbp_game.home_outcome = gpf.get_home_outcome(pbp_data)
            pbp_game.home_score = int(pbp_data[-1].home_score)
            pbp_game.away_score = int(pbp_data[-1].away_score)

            for st in pbp_data:
                pbp_game.pbp_stats.append(st)
            print 'pbp stats successful'
        except Exception, e:
            traceback.print_exc()
            #problem processing box data
            pbp_error_msg = "pbp stats failed: %s, %s, %s" % (date_string, raw_game.home_team, raw_game.away_team)
            db.session.rollback()
            errors.append(pbp_error_msg)
            continue
        #save to database
        the_year.games.append(pbp_game)
        db.session.flush()

        #check the pbp stats against the box stats
        check_stats_errors = gpf.check_game_stats(pbp_game,current_year)
        if len(check_stats_errors) > 6:
            #if more than 6 players had stats errors
            send_errors('check stats error'+date_string,check_stats_errors)
            pass

        #check the possession time
        poss_time, poss_error = gpf.check_poss_time(pbp_game, current_year)
        if poss_error > 30:
            errors.append('possesion time error: %s, %s, %s, %s, %s' % (poss_time, poss_error, pbp_game.home_team, pbp_game.away_team, date_string))

        db.session.commit()
    return errors

def store_raw_scoreboard_games(the_date, teamIDs = []):

    errors = []
    try:
        date_string = datetime.strftime(the_date,'%m/%d/%Y')
    except:
        #bad date, failed getting any games
        errors.append('bad date given')
        return errors

    try:
        #get the list of teams, box game links, and pbp links from the day's scoreboard
        teams, box_links, links, msg = tf.get_scoreboard_games(date_string, current_year)

        if teams == None:
            #getting the scoreboard links failed, failed getting any games
            assert False

        #only use certain teams
        if teamIDs != []:
            ind = []
            for j in range(len(teams)):
                if teams[j][0] in teamIDs or teams[j][1] in teamIDs:
                    ind.append(j)
            teams = [teams[i] for i in ind]
            box_links = [box_links[i] for i in ind]
            links = [links[i] for i in ind]
    except:
        errors.append('failed to get scoreboard links')
        return errors
        pass

    #iterate through games
    for j in range(len(teams)):
        try:
            #these will be error free because of the error checking previously
            #TODO: the teams are going to be ncaaIDs coming form tf.get_scoreboard_games, not ncaa names, so the latter part of this will fail if the team is in the db
            team1 = teams[j][0]
            team1_obj = models.team.query.join(models.year).filter(and_(models.year.year==current_year,models.team.ncaaID==team1)).first()
            team2 = teams[j][1]
            team2_obj = models.team.query.join(models.year).filter(and_(models.year.year==current_year,models.team.ncaaID==team2)).first()
            link = links[j]
            box_link = box_links[j]

            if team1_obj == None:
                team1_ncaa = team1
                team1_ncaaID = team1
                print team1
            else:
                team1_ncaa = team1_obj.ncaa
                team1_ncaaID = team1_obj.ncaaID
            if team2_obj == None:
                team2_ncaa = team2
                team2_ncaaID = team2
                print team2
            else:
                team2_ncaa = team2_obj.ncaa
                team2_ncaaID = team2_obj.ncaaID
        except:
            errors.append('failed getting soup data at index: ' + str(j))
            #continue in the loop
            continue

        store_raw_data_errors = store_raw_game(box_link,link,the_date,date_string,team1_ncaa,team1_ncaaID,team2_ncaa,team2_ncaaID)
        errors += store_raw_data_errors
        if len(store_raw_data_errors) == 0:
            #data stored successfully
            print team1_ncaa, team2_ncaa


    return errors

def store_raw_game(box_link, pbp_link, date,date_string, team1_ncaa, team1_ncaaID, team2_ncaa, team2_ncaaID):
    '''Given box score link, pbp link, date, and two teams, this function
    stores the raw html rows in the database'''


    #msg holds information about the success of this function
    errors = []

    #check if game exists
    game_exists_q = models.raw_game.query.filter(or_(and_(models.raw_game.home_team==team1_ncaaID,models.raw_game.away_team==team2_ncaaID,models.raw_game.date==date),
                                      and_(models.raw_game.home_team==team2_ncaaID,models.raw_game.away_team==team1_ncaaID,models.raw_game.date==date))).first()

    #if the game was found in the database then delete previous stats for it
    if game_exists_q != None:
        this_game = game_exists_q
        this_game.raw_box_stats.delete()
        this_game.raw_pbp_stats.delete()
    else:
        #create the new raw_game instance
        this_game = models.raw_game()
        this_game.date = date

    #query for the year object
    the_year =  models.year.query.filter(models.year.year==current_year).first()

    if the_year == None:
        #no year found, create it
        the_year = models.year()
        the_year.year = db_year
        db.session.add(the_year)
        db.session.commit()

    try:
        #get the box_data
        box_soup = lf.get_soup(box_link)
        box_rows = tf.get_box_rows(box_soup)

        if box_rows == None:
            #throw an error
            assert False

        for row in box_rows:
            #make the raw box row to hold the soup
            raw_box_row = models.raw_box()
            raw_box_row.soup_string = str(row)

            #append the child row to the raw game instance
            this_game.raw_box_stats.append(raw_box_row)
    except:
        #error with the box rows
        errors.append('error retrieving box rows: '+",".join([team1_ncaa,team2_ncaa,date_string]))

    try:
        #get the pbp_data
        pbp_soup = lf.get_soup(pbp_link)
        rows = tf.get_pbp_rows(pbp_soup)
        if rows == None:
            #throw an error
            assert False

        for row in rows:
            #make the raw pbp row to hold the soup
            raw_pbp_row = models.raw_play()
            raw_pbp_row.soup_string = str(row)

            #append the child row to the raw game instance
            this_game.raw_pbp_stats.append(raw_pbp_row)

        #get the home and away teams from pbp link
        home_team, away_team = tf.home_and_away_teams(pbp_soup,team1_ncaa,team2_ncaa)

        if home_team != None:
            if home_team == team1_ncaa:
                this_game.home_team = team1_ncaaID
                this_game.away_team = team2_ncaaID
            else:
                this_game.home_team = team2_ncaaID
                this_game.away_team = team1_ncaaID
        else:
            errors.append('error with home and away teams')
            assert False
    except:
        #error retrieving pbp rows
        errors.append('error retrieving pbp rows: '+",".join([team1_ncaa,team2_ncaa,date_string]))

    if len(errors) == 0:
        the_year.raw_games.append(this_game)
        db.session.commit()
    else:
        db.session.rollback()
    return errors
def send_mail(to_address,subject,msg):
    attempts = 0

    while attempts < 3:
        try:
            from_address = 'stats.mbb@gmail.com'
            #to_address  = 'seth.hendrickson16@gmail.com'

            message = 'Subject: %s\n\n%s' % (subject, msg)

            # Credentials (if needed)
            username = 'stats.mbb@gmail.com'
            password = 'St314ats'

            # The actual mail send
            server = smtplib.SMTP('smtp.gmail.com:587')
            #server.ehlo()
            server.starttls()
            server.login(username,password)
            server.sendmail(from_address, to_address, message)
            server.quit()
            break
        except:
            attempts += 1

def send_errors(subject,errors):
    msg = ''
    for e in errors:
        try:
            msg += e + '\n'
        except:
            continue
    send_mail('seth.hendrickson16@gmail.com',subject,msg)
#custom errors
class rawGameException(Exception):
    pass
class rawGamesScoreboardException(Exception):
    pass
class pbpGameException(Exception):
    pass

if __name__ == "__main__":
    main()