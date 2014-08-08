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
from datetime import datetime
from mysite import models
from mysite import db
from mysite import link_functions as lf
import smtplib, traceback

#global year constant
db_year = 2014

def main():
    '''This function needs to do all the one time things that are required
    to begin a new database for a new season'''

    #use today's date
    the_date = datetime.today().date()

    date_string = '03/10/2014'
    the_date = datetime.strptime(date_string,'%m/%d/%Y').date()

    #update_db(the_date)

    '''new_year = models.year()
    new_year.year = 2014
    db.session.add(new_year)
    db.session.commit()'''

    #return None
    #q = models.team.query.filter(getattr(models.team,'ncaaID')=='8').first()
    #print q.statsheet
    q = models.team.query.all()
    print len(q)
    return None
    for play in q:
        #db.session.delete(play)
        print play.player
        continue
        home_team = tf.get_team_param(game.home_team,'ncaaID').statsheet
        away_team = tf.get_team_param(game.away_team,'ncaaID').statsheet
        print home_team, away_team, game.date
        #db.session.delete(game)
    #db.session.commit()
    return None

def update_db(the_date):
    '''This function is to be called once a day to update the games in
    the database. Does it need to handle failures of the previous day(s)
    updates? Or would that be a manual thing that could be done? Have the function
    send admin an email if the update fails.
    '''

    #store all the raw html for games for the date in the database
    store_raw_scoreboard_games_bool = store_raw_scoreboard_games(the_date)
    #return None
    if not store_raw_scoreboard_games_bool:
        print store_raw_scoreboard_games_bool
        return None

    #return None

    #update the team info (rpi, sos, etc...)
    #tf.get_rpi()

    #process the day's raw games into data
    process_raw_games(the_date)
def process_raw_games(the_date):
    try:
        date_string = datetime.strftime(the_date,'%m/%d/%Y')
    except:
        date_string = 'bad date'
        pass

    #query the raw database for all of the games for the date used
    raw_q = models.raw_game.query.filter(models.raw_game.date==the_date).all()

    #query for the year object to add the games to
    the_year =  models.year.query.filter(models.year.year==db_year).first()

    if the_year == None:
        return None

    error_msg = ''
    for raw_game in raw_q:


        pbp_error_msg = ''
        #if the team info doesn't exist for the team skip it
        #TODO: get_team_param no longer works, or does it?
        home_team_obj = tf.get_team_param(raw_game.home_team, 'ncaaID')
        away_team_obj = tf.get_team_param(raw_game.away_team, 'ncaaID')

        if home_team_obj == None or away_team_obj == None:
            pbp_error_msg += "couldn't find one or more teams, %s, %s, %s" % (date_string, raw_game.home_team, raw_game.away_team)
            continue

        #TODO
        #see if the pbp game already exists
        this_game = models.game.query.filter(or_(and_(models.game.date==the_date,models.game.home_team==home_team_obj.ncaaID,models.game.away_team==away_team_obj.ncaaID),
                                            and_(models.game.date==the_date,models.game.away_team==home_team_obj.ncaaID,models.game.home_team==away_team_obj.ncaaID))).first()
        if this_game != None:
            #the game exists
            if this_game.neutral_site:
                #if it's a neutral site game, then update the home and away teams
                this_game.home_team = raw_game.home_team
                this_game.away_team = raw_game.away_team
        else:
            #the game doesn't exist
            pbp_game = models.game()
            pbp_game.home_team = raw_game.home_team
            pbp_game.away_team = raw_game.away_team
            pbp_game.home_outcome = raw_game.home_outcome
            pbp_game.date = raw_game.date
            #check if it is a neutral site game
                #check the team's schedule page for this date


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
        except Exception, e:
            traceback.print_exc()
            #problem processing box data
            pbp_error_msg = "box stats failed, %s, %s, %s" % (date_string, raw_game.home_team, raw_game.away_team)
            db.session.rollback()
            error_msg += "\n"+pbp_error_msg
            continue

        try:
            pbp_rows = models.raw_play.query.join(models.raw_game).filter(and_(models.raw_game.home_team==raw_game.home_team,models.raw_game.away_team==raw_game.away_team,models.raw_game.date==raw_game.date)).all()
            if pbp_rows == None:
                #TODO: should I do something different here, to just say that there weren't any raw data rows?
                assert False
            pbp_rows = [pbp_row.soup_string for pbp_row in pbp_rows]
            #process the play by play data for the game
            pbp_data = gpf.get_play_by_play(raw_game.home_team,raw_game.away_team,raw_game.date, pbp_rows,starters)
            for st in pbp_data:
                pbp_game.pbp_stats.append(st)
        except Exception, e:
            traceback.print_exc()
            #problem processing pbp data
            pbp_error_msg = "pbp stats failed, %s, %s, %s" % (date_string, raw_game.home_team, raw_game.away_team)
            db.session.rollback()
            error_msg += "\n"+pbp_error_msg
            #continue
            break

        the_year.games.append(pbp_game)
        db.session.flush()
        db.session.commit()

    #if there was an error, send email
    if error_msg != '':
        print error_msg
        send_mail('seth.hendrickson16@gmail.com',date_string,error_msg)


def store_raw_scoreboard_games(the_date):
    try:
        try:
            date_string = datetime.strftime(the_date,'%m/%d/%Y')
        except:
            #bad date, failed getting any games
            raise rawGamesScoreboardException, 'bad date given'

        #get the list of teams, box game links, and pbp links from the day's scoreboard
        teams, box_links, links, msg = tf.get_scoreboard_games(date_string)

        if teams == None:
            #getting the scoreboard links failed, failed getting any games
            raise rawGamesScoreboardException, "Getting scoreboard games failed: " + msg

        #iterate through games
        raw_game_error_msg = ''
        for j in range(len(teams)):
            try:
                #these will be error free because of the error checking previously
                team1 = teams[j][0]
                team1_obj = tf.get_team_param(team1,'ncaaID')
                team2 = teams[j][1]
                team2_obj = tf.get_team_param(team2,'ncaaID')
                link = links[j]
                box_link = box_links[j]


                if team1_obj == None or team2_obj == None:
                    raise rawGameException, 'one or more teams not found'



                #if game is in database skip it
                game_exists_q = models.raw_game.query.filter(or_(and_(models.raw_game.home_team==team1,models.raw_game.away_team==team2,models.raw_game.date==the_date),
                                                  and_(models.raw_game.home_team==team2,models.raw_game.away_team==team1,models.raw_game.date==the_date))).first()

                #if the game was found in the database then skip this link
                if game_exists_q != None:
                    print game_exists_q.home_team
                    continue

                store_raw_data_msg = store_raw_game(box_link,link,the_date,team1_obj,team2_obj)
                if store_raw_data_msg != None:
                    #error with storing data, add to failed games
                    raise rawGameException, store_raw_data_msg
                else:
                    #data stored successfully
                    pass
            except rawGameException, e:
                #print the error message, and continue in the loop
                raw_game_error_msg += str(e)+'\n'
                print e
                continue

        #send an email with the failed games if there were any
        if raw_game_error_msg != '':
            send_mail('seth.hendrickson16@gmail.com',date_string+', '+'raw',raw_game_error_msg)

        #return True, indicating at least one game stored successfully
        return True
    except rawGamesScoreboardException,e:
        send_mail('seth.hendrickson16@gmail.com',date_string+', '+'raw',str(e))
        print e
        return False

def store_raw_game(box_link, pbp_link, date, team1, team2):
    '''Given box score link, pbp link, date, and two teams, this function
    stores the raw html rows in the database'''

    #msg holds information about the success of this function
    msg = ''

    #query for the year object
    the_year =  models.year.query.filter(models.year.year==db_year).first()

    if the_year == None:
        #no year found, create it
        the_year = models.year()
        the_year.year = db_year
        db.session.add(the_year)
        db.session.commit()

    #create the new raw_game instance
    this_game = models.raw_game()

    this_game.date = date

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
        msg += "; error retrieving box rows"+",".join([team1.statsheet,team2.statsheet])

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
        home_team, away_team = tf.home_and_away_teams(pbp_soup,team1.ncaa,team2.ncaa)

        if home_team != None:
            home_team_obj = tf.get_team_param(home_team,'ncaa')
            away_team_obj = tf.get_team_param(away_team,'ncaa')

            this_game.home_team = home_team_obj.ncaaID
            this_game.away_team = away_team_obj.ncaaID
        else:
            msg += "; error with home and away teams"
            assert False
    except:
        #error retrieving pbp rows
        msg += "; error retrieving pbp rows: "+",".join([team1.statsheet,team2.statsheet])

    if msg == '':
        the_year.raw_games.append(this_game)
        #db.session.add(this_game)
        db.session.commit()
        return None
    else:
        db.session.rollback()
        return msg
def send_mail(to_address,subject,msg):
    from_address = 'seth.hendrickson16@gmail.com'
    #to_address  = 'seth.hendrickson16@gmail.com'

    message = 'Subject: %s\n\n%s' % (subject, msg)

    # Credentials (if needed)
    username = 'seth.hendrickson16@gmail.com'
    password = 'Ros16eit'

    # The actual mail send
    server = smtplib.SMTP('smtp.gmail.com:587')
    #server.ehlo()
    server.starttls()
    server.login(username,password)
    server.sendmail(from_address, to_address, message)
    server.quit()

#custom errors
class rawGameException(Exception):
    pass
class rawGamesScoreboardException(Exception):
    pass
class pbpGameException(Exception):
    pass

if __name__ == "__main__":
    main()