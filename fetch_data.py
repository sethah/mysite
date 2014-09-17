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
from sqlalchemy.sql import func, select
from mysite import models, db
from mysite import team_info_functions as tf
from mysite import game_process_functions as gpf
from mysite import data_functions as df
from datetime import datetime
from mysite import db
import time
from mysite import link_functions as lf
import smtplib, traceback
import cProfile
import StringIO
import pstats
import contextlib

current_year = df.get_year()

@contextlib.contextmanager
def profiled():
    pr = cProfile.Profile()
    pr.enable()
    yield
    pr.disable()
    s = StringIO.StringIO()
    ps = pstats.Stats(pr, stream=s).sort_stats('cumulative')
    ps.print_stats()
    # uncomment this to see who's calling what
    # ps.print_callers()
    #print s.getvalue()
    print s.getvalue()[0:10000]
def main():
    '''This function needs to do all the one time things that are required
    to begin a new database for a new season'''

    #use today's date
    teams = models.team.query.all()
    cnt = 0
    '''for team in teams:
        keys = team.__dict__.keys()
        for k in keys:
            att = getattr(team,k)
            print k,att,type(att)
            if type(att) == type(u'a'):
                cnt += 1
        team.statsheet = team.statsheet.encode('ascii','ignore')
        if type(att) == type(u'a') and False:
            print type(att.encode('ascii','ignore'))
            setattr(team,k,att.encode('ascii','ignore'))
            print type(getattr(team,k))
        break
    print cnt
    db.session.commit()
    try:
        team.ncaaID = team.ncaaID.encode('ascii','ignore')
        team.statsheet = team.statsheet.encode('ascii','ignore')
        team.ncaa = team.ncaa.encode('ascii','ignore')
        team.espn_name = team.espn_name.encode('ascii','ignore')
        team.espn = team.espn.encode('ascii','ignore')
        team.cbs1 = team.cbs1.encode('ascii','ignore')
        team.cbs2 = team.cbs2.encode('ascii','ignore')
        team.rpi_rank = team.rpi_rank.encode('ascii','ignore')
        team.wins = team.wins.encode('ascii','ignore')
        team.losses = team.losses.encode('ascii','ignore')
        team.rpi = team.rpi.encode('ascii','ignore')
        team.sos = team.sos.encode('ascii','ignore')
        team.sos_rank = team.sos_rank.encode('ascii','ignore')
        team.conference = team.conference.encode('ascii','ignore')
    except:
        continue'''
    #db.session.commit()
    with profiled():
        a = time.time()
        q1 = models.game.query.all()
        #q1 = db.session.query(models.game.home_team).all()
        b = time.time()
        #q1 = select([models.pbp_stat]).where(models.pbp_stat.player=='NOAH VONLEH')
        #db.engine.execute(q1)
        c = time.time()
    #print q1
    print len(q1)
    return None
    q = models.pbp_stat.query.with_entities(models.pbp_stat.worth,models.pbp_stat.stat_type).join(models.game).filter(or_(models.game.away_team == team_obj.ncaaID, models.game.home_team == team_obj.ncaaID)).all()
    #get all the games for this team
    a = time.time()
    q1 = models.pbp_stat.query.with_entities(models.pbp_stat.worth,models.pbp_stat.stat_type).join(models.game).filter(or_(models.game.away_team == team_obj.ncaaID, models.game.home_team == team_obj.ncaaID)).all()
    b = time.time()
    print b-a


    s = 0
    x=0
    for st in q1.all():
        if st.possession_time_adj < 10 and st.possession_time_adj>0:
            s += st.home_score
        elif st.possession_time_adj>=10 and st.possession_time_adj<=20:
            x += st.home_score

    print x
    b = time.time()
    #q2 = db.session.query(models.pbp_stat,func.sum(models.pbp_stat.home_score).label('total score'))
    #q3 = models.pbp_stat.query
    qa = db.session.query(models.pbp_stat,func.sum(models.pbp_stat.home_score).label('total score')).join(models.game).filter(or_(models.game.away_team == team_obj.ncaaID, models.game.home_team == team_obj.ncaaID)).filter(models.pbp_stat.possession_time_adj.between(0,10))
    qb = db.session.query(models.pbp_stat,func.sum(models.pbp_stat.home_score).label('total score')).join(models.game).filter(or_(models.game.away_team == team_obj.ncaaID, models.game.home_team == team_obj.ncaaID)).filter(models.pbp_stat.possession_time_adj.between(10,20))
    qc = db.session.query(models.pbp_stat,func.sum(models.pbp_stat.home_score).label('total score')).join(models.game).filter(or_(models.game.away_team == team_obj.ncaaID, models.game.home_team == team_obj.ncaaID)).filter(models.pbp_stat.possession_time_adj.between(20,30))
    qd = db.session.query(models.pbp_stat,func.sum(models.pbp_stat.home_score).label('total score')).join(models.game).filter(or_(models.game.away_team == team_obj.ncaaID, models.game.home_team == team_obj.ncaaID)).filter(models.pbp_stat.possession_time_adj.between(30,40))
    print qa.all(),qb.all(),qc.all(),qd.all()
    c = time.time()
    print c-b,b-a



    return None
    the_date = datetime.today().date()

    date_string = '03/13/2014'
    the_date = datetime.strptime(date_string,'%m/%d/%Y').date()

    update_db(the_date)
    return None

def update_db(the_date):
    '''This function is to be called once a day to update the games in
    the database.
    '''
    try:
        date_string = datetime.strftime(the_date,'%m/%d/%Y')
    except:
        return None

    #limit update games to certain teams, all teams if empty
    update_teams = ['306']

    #store all the raw html for games for the date in the database
    store_raw_scoreboard_games_errors = store_raw_scoreboard_games(the_date,update_teams)
    if len(store_raw_scoreboard_games_errors) > 0:
        #call function to email the error list
        send_errors('raw game errors '+date_string,store_raw_scoreboard_games_errors)
        for e in store_raw_scoreboard_games_errors:
            print e
        pass
        return None
    #return None
    #update the team info (rpi, sos, etc...)
    #TODO: PA won't connect to statsheet
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
    '''
    @Function: process_raw_games(the_date,update_teams = [])
    @Author: Seth Hendrickson, 8/26/14
    @Summary: query the database for the raw games for a given date, and turn
    them into play by play games.
    '''
    errors = []

    try:
        date_string = datetime.strftime(the_date,'%m/%d/%Y')
    except:
        errors.append('bad date')
        return errors

    #query the raw database for all of the games for the date used
    q = tf.query_by_year('raw_game',current_year)
    raw_q = q.filter(models.raw_game.date==the_date).all()
    if raw_q == None:
        errors.append('No raw games found for this date, %s' % date_string)
        return errors

    #query for the year object to add the games to
    the_year = tf.query_by_year('year',current_year).first()
    if the_year == None:
        errors.append('No year found for pbp processing')
        return errors

    for raw_game in raw_q:
        #get the database year from the game's date
        game_year = df.get_year_from_date(raw_game.date)

        if update_teams != []:
            #skip teams that are not in the update list
            if raw_game.home_team not in update_teams and raw_game.away_team not in update_teams:
                continue
        try:
            #get the game or create it, and delete existing stats
            pbp_game, new_game = models.game.get_or_create(the_date,raw_game.home_team,raw_game.away_team, raw_game.home_outcome)
            if new_game:
                pbp_game.neutral_site = tf.is_neutral(pbp_game.date,pbp_game.home_team,pbp_game.away_team)
            pbp_game.box_stats.delete()
            pbp_game.pbp_stats.delete()
            db.session.flush()

            #check if one of the teams is not in the database, process wout stats
            home_team_obj = tf.query_by_year('team',game_year).filter(models.team.ncaaID==raw_game.home_team).first()
            away_team_obj = tf.query_by_year('team',game_year).filter(models.team.ncaaID==raw_game.away_team).first()
            if home_team_obj == None or away_team_obj == None:
                no_stats(raw_game, pbp_game)
                db.session.commit()
                continue

        except Exception, e:
            traceback.print_exc()
            #error instantiating new pbp game
            errors.append('failed to instantiate new game for: %s, %s, %s' % (raw_game.home_team, raw_game.away_team, date_string))
            continue

        try:
            starters = process_box(raw_game, pbp_game)
        except Exception, e:
            traceback.print_exc()
            #problem processing box data
            box_error_msg = "box stats failed: %s, %s, %s" % (raw_game.date_string(), raw_game.home_team, raw_game.away_team)
            db.session.rollback()
            errors.append(box_error_msg)
            continue

        try:
            process_pbp(raw_game, pbp_game, starters)
        except Exception, e:
            traceback.print_exc()
            #problem processing box data
            pbp_error_msg = "pbp stats failed: %s, %s, %s" % (raw_game.date_string(), raw_game.home_team, raw_game.away_team)
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
        if abs(poss_error) > 30:
            errors.append('possesion time error: %s, %s, %s, %s, %s' % (poss_time, poss_error, pbp_game.home_team, pbp_game.away_team, date_string))

        db.session.commit()
    return errors
def no_stats(raw_game, pbp_game):
    #if both teams don't exist in the database, then assign a win/loss and continue
    pbp_rows = raw_game.raw_pbp_stats.all()
    pbp_rows = [pbp_row.soup_string for pbp_row in pbp_rows]
    pbp_data = gpf.get_play_by_play(raw_game.home_team,raw_game.away_team,raw_game.date, pbp_rows,[])

    #assign some score attributes to the game
    pbp_game.home_outcome = gpf.get_home_outcome(pbp_data)
    pbp_game.home_score = int(pbp_data[-1].home_score)
    pbp_game.away_score = int(pbp_data[-1].away_score)

    db.session.flush()
def process_pbp(raw_game, pbp_game, starters):
    pbp_rows = models.raw_play.query.join(models.raw_game).filter(and_(models.raw_game.home_team==raw_game.home_team,models.raw_game.away_team==raw_game.away_team,models.raw_game.date==raw_game.date)).all()
    if pbp_rows == None:
        assert False

    #get list of pbp row strings
    pbp_rows = [pbp_row.soup_string for pbp_row in pbp_rows]

    #process the play by play data for the game
    pbp_data = gpf.get_play_by_play(raw_game.home_team,raw_game.away_team,raw_game.date, pbp_rows,starters)

    #assign some score attributes to the game
    if raw_game.home_outcome != None:
        pbp_game.home_outcome = raw_game.home_outcome
    else:
        pbp_game.home_outcome = gpf.get_home_outcome(pbp_data)
    pbp_game.home_score = int(pbp_data[-1].home_score)
    pbp_game.away_score = int(pbp_data[-1].away_score)

    for st in pbp_data:
        pbp_game.pbp_stats.append(st)
    print 'pbp stats successful'
    db.session.flush()
def process_box(raw_game, pbp_game):
    #process the raw box score data for the game
    box_rows = models.raw_box.query.join(models.raw_game).filter(and_(models.raw_game.home_team==raw_game.home_team,models.raw_game.away_team==raw_game.away_team,models.raw_game.date==raw_game.date)).all()
    if box_rows == None:
        assert False

    #get a list of the box row strings
    box_rows = [box_row.soup_string for box_row in box_rows]

    #process the rows of the box data into box stat objects
    box_data = gpf.raw_box_to_stats(raw_game.home_team,raw_game.away_team,raw_game.home_outcome,raw_game.date,box_rows)            #store it
    for st in box_data:
        pbp_game.box_stats.append(st)

    #assign the starters for the game
    starters = []
    for plr in box_data:
        if plr.started:
            starters.append(plr.name)
    print 'box stats successful'
    db.session.flush()

    return starters
def store_raw_scoreboard_games(the_date, teamIDs = []):
    '''
    @Function: store_raw_scoreboard_games(the_date, teamIDs = [])
    @Author: Seth Hendrickson, 8/26/14
    @Summary: get all the games from the ncaa website scoreboard for a given date,
    then grab all the raw data from each game and store it in the database
    '''

    errors = []
    try:
        date_string = datetime.strftime(the_date,'%m/%d/%Y')
    except:
        #bad date, failed getting any games
        errors.append('bad date given')
        return errors
    db_year = df.get_year_from_date(the_date)

    try:
        #get the list of teams, box game links, and pbp links from the day's scoreboard
        teams, box_links, links, msg = tf.get_scoreboard_games(date_string, current_year)
        print teams

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
            team1_ncaa, team1_ncaaID, team2_ncaa, team2_ncaaID = get_scoreboard_teams(teams[j], db_year)
        except Exception, e:
            traceback.print_exc()
            errors.append('failed getting soup data at index: ' + str(j))
            #continue in the loop
            continue

        store_raw_data_errors = store_raw_game(box_links[j],links[j],the_date,date_string,team1_ncaa,team1_ncaaID,team2_ncaa,team2_ncaaID)
        errors += store_raw_data_errors
        if len(store_raw_data_errors) == 0:
            #data stored successfully
            print team1_ncaa, team2_ncaa
    return errors
def get_scoreboard_teams(teams, db_year):
    team1 = teams[0]
    q = tf.query_by_year('team',db_year)
    team1_obj = q.filter(models.team.ncaaID==team1).first()

    team2 = teams[1]
    q = tf.query_by_year('team',db_year)
    team2_obj = q.filter(models.team.ncaaID==team2).first()

    if team1_obj == None:
        team1_ncaa = team1
        team1_ncaaID = team1
    else:
        team1_ncaa = team1_obj.ncaa
        team1_ncaaID = team1_obj.ncaaID
    if team2_obj == None:
        team2_ncaa = team2
        team2_ncaaID = team2
    else:
        team2_ncaa = team2_obj.ncaa
        team2_ncaaID = team2_obj.ncaaID

    return team1_ncaa, team1_ncaaID, team2_ncaa, team2_ncaaID
def store_raw_game(box_link, pbp_link, date,date_string, team1_ncaa, team1_ncaaID, team2_ncaa, team2_ncaaID):
    '''Given box score link, pbp link, date, and two teams, this function
    stores the raw html rows in the database'''

    db_year = df.get_year_from_date(date)

    #msg holds information about the success of this function
    errors = []

    this_game = models.raw_game.get_or_create(date, team1_ncaaID, team2_ncaaID)
    this_game.raw_box_stats.delete()
    this_game.raw_pbp_stats.delete()

    #query for the year object
    the_year = models.year.get_or_create(db_year)
    db.session.flush()

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
        this_game.home_outcome = tf.get_home_outcome(rows)

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
        #team1_ncaa, team1_ncaaID, team2_ncaa, team2_ncaaID
        this_game.home_team, this_game.away_team = tf.home_and_away_teams(pbp_soup,team1_ncaa, team1_ncaaID, team2_ncaa, team2_ncaaID)

    except Exception:
        traceback.print_exc()
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
    send_mail('stats.mbb@gmail.com',subject,msg)

if __name__ == "__main__":
    main()