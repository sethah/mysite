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

from mysite import models
from mysite import db
from mysite import link_functions as lf
from mysite import team_info_functions as tf
from sqlalchemy import and_, or_
import datetime
import traceback

def main():
    return None
    #get_ncaa_schedule_data('306')
    #return None
    '''q = models.year.query.all()
    print len(q)
    return None
    for year in q:
        if year.year == None:
            db.session.delete(year)
    db.session.commit()'''
    '''
    q = models.team.query.all()
    q = models.game.query.all()
    cnt = 0
    for game in q:
        try:
            home_team_id = int(game.home_team)
            home_team = models.team.query.join(models.year).filter(and_(models.year.year==2014,models.team.ncaaID==game.home_team)).first()
            if home_team is None:
                #print home_team
                cnt += 1
                db.session.delete(game.box_stats)
                db.session.delete(game.pbp_stats)
                db.session.delete(game)
            away_team = models.team.query.join(models.year).filter(and_(models.year.year==2014,models.team.ncaaID==game.away_team)).first()
            if away_team is None:
                cnt += 1
                #print away_team
                db.session.delete(game.box_stats)
                db.session.delete(game.pbp_stats)
                db.session.delete(game)
        except:
            #it's a string skip it
            continue
    print cnt
    #db.session.rollback()
    db.session.commit()
    return None'''

    yearly_update_schedules(current_year,360,30)
def yearly_update_schedules(year_arg,q_offset,q_limit=10):
    all_teams = models.team.query.join(models.year).filter(models.year.year==year_arg).limit(q_limit).offset(q_offset).all()
    for team in all_teams:
        locations, opponents, dates = tf.get_ncaa_schedule_data(team.ncaaID)
        print team.statsheet

        if locations == None:
            continue

        store_schedule(team.ncaaID,locations,opponents,dates,year_arg)

def store_schedule(teamID,locations,opponents,dates,year_arg):
    #query for the year object to add the games to
    the_year =  models.year.query.filter(models.year.year==year_arg).first()
    if the_year == None:
        print 'no year found'
        return None

    #loop through all games
    for j in range(len(locations)):
        try:
            #check to see if this game already exists
            q = models.game.query.filter(or_(and_(models.game.date==dates[j],models.game.home_team==teamID,models.game.away_team==opponents[j]),
                                            and_(models.game.date==dates[j],models.game.away_team==teamID,models.game.home_team==opponents[j]))).first()
            if q != None:
                #continue if game already exists
                continue
                new_game = q
            else:
                new_game = models.game()

            new_game.date = dates[j]
            if locations[j] == 'Home':
                new_game.home_team = teamID
                new_game.away_team = opponents[j]
                new_game.neutral_site = False
            elif locations[j] == 'Away':
                new_game.away_team = teamID
                new_game.home_team = opponents[j]
                new_game.neutral_site = False
            elif locations[j] == 'Neutral':
                #if it's a neutral game, then the home/away teams are arbitrary
                new_game.home_team = teamID
                new_game.away_team = opponents[j]
                new_game.neutral_site = True

            the_year.games.append(new_game)
        except:
            traceback.print_exc()
            return None
            print 'failed storing game on: '
            db.session.rollback()

    db.session.commit()

def yearly_update_rosters(year_arg,max_count=10):
    all_teams = models.team.query.join(models.year).filter(models.year.year==year_arg).all()
    count = 0
    for team in all_teams:
        #if team doesn't have any players and count < count
        #get all the players for this team
        plr_q = models.player.query.join(models.team).join(models.year).filter(and_(models.year.year==year_arg,models.team.ncaaID==team.ncaaID)).all()
        if len(plr_q) == 0 and count < max_count:
            store_roster(team.ncaaID,year_arg)
            print team.statsheet
            count += 1
    return None
def get_all_teams(year):
    '''this function should be called once/year to get all the division I teams
    from the ncaa team website'''

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
    '''this function should be called once a year to delete teams that are no
    longer D1 and to add new D1 teams'''

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
    #delete the new teamID and print it
    for team in all_teams:
        if team not in all_teams_new:
            delete_team = models.raw_team.query.filter(models.raw_team.ncaaID==team).first()
            db.session.delete(delete_team)
            print 'deleted: '+team
    db.session.commit()
def create_data_db():
    #create the database if it doesn't exist, then query it for all the teams in it
    bind_key = 'data_db'
    try:
        assert False
        all_teams = models.team.query.all()
        all_teams = [team.ncaaID for team in all_teams]
    except:
        db.create_all(bind=[bind_key])
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
def teams_static_to_data(current_year):
    print len(models.team.query.all())
    static_teams = models.raw_team.query.all()

    #see if the year has a table yet
    year_q = models.year.query.filter(models.year.year == current_year).first()
    if year_q == None:
        year_obj = models.year()
    else:
        year_obj = year_q
        #clear out the teams that exist for the year
        existing_teams = models.team.query.join(models.year).filter(models.year==current_year).all()
        for team in existing_teams:
            db.session.delete(team)

    #copy the static teams to the sql data db
    for team in static_teams:
        new_team = models.team()
        new_team.statsheet = team.statsheet
        new_team.espn = team.espn
        new_team.espn_name = team.espn_name
        new_team.ncaaID = team.ncaaID
        new_team.ncaa = team.ncaa
        new_team.cbs1 = team.cbs1
        new_team.cbs2 = team.cbs2
        db.session.add(new_team)
        year_obj.teams.append(new_team)

    #commit the changes
    db.session.commit()
def store_roster(teamID,year_arg):
    '''
    @Function: store_roster(teamID)
    @Author: S. Hendrickson 3/5/14
    @Return: This function stores a team's roster in the database
    '''
    the_team = models.team.query.join(models.year).filter(and_(models.year.year==year_arg,models.team.ncaaID==teamID)).first()

    if the_team==None:
        print 'team not found: %s' % teamID
        return None

    try:
        #query for all players that belong to this team
        q = models.player.query.join(models.team).join(models.year).filter(and_(models.team.ncaaID==teamID,models.year.year==year_arg)).all()

        #delete the players that exist
        for plr in q:
            print plr.name
            db.session.delete(plr)

        #store the team's roster
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
                name, first_name, last_name = tf.convert_name_ncaa(name)
                first_names.append(first_name)
                last_names.append(last_name)
                names.append(first_name+' '+last_name)

        for j in range(len(names)):
            try:
                new_player = models.player()
                new_player.first_name = first_names[j]
                new_player.last_name = last_names[j]
                new_player.name = names[j]
                print new_player.name
                new_player.position = positions[j]
                new_player.height = heights[j]
                new_player.pclass = pclasses[j]
                the_team.players.append(new_player)
                db.session.commit()
            except:
                db.session.rollback()
                traceback.print_exc()
                print 'error adding new player'
                continue
    except:
        print 'failed getting roster for team: %s' % the_team.statsheet
        return None
def store_rosters(teamIDs, year_arg):
    '''
    @Function: store_rosters(teamIDs)
    @Author: S. Hendrickson 3/5/14
    @Return: This function stores a team's roster and other various info and
    stores it in a database
    '''

    for teamID in teamIDs:
        the_team = tf.get_team_param(teamID,'ncaaID')

        if the_team==None:
            print 'team not found: %s' % teamID
            continue

        try:
            #query for all players that belong to this team
            q = models.player.query.join(models.team).join(models.year).filter(and_(models.team.ncaaID==teamID,models.year.year==year_arg)).all()

            #delete the players that exist
            for plr in q:
                print plr.name
                db.session.delete(plr)

            #store the team's roster
            store_roster(teamID,year_arg)
        except:
            print 'failed getting roster for team: %s' % the_team.statsheet
            continue

if __name__ == "__main__":
    main()