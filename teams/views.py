from flask import render_template, flash, redirect, session, url_for, request, g, send_file, Blueprint
from mysite import models, db
import chart_functions as cf
import error_functions as ef
import data_functions as df
import team_info_functions as tf
from sqlalchemy import and_, or_
from sqlalchemy.sql import func
from datetime import datetime
import time
import json

current_year = df.get_year()

mod = Blueprint('teams', __name__,url_prefix='/teams')
@mod.route('/', defaults={'conference': None})
@mod.route('/')
def teams():

    #need to query all teams to get all possible conferences for the dropdown
    all_teams = models.team.query.join(models.year).filter(models.year.year==current_year).all()

    #get the conferences
    conferences = []
    for tm in all_teams:
        if tm.conference not in conferences:
            conferences.append(tm.conference)
    conferences = ['All']+sorted(conferences)

    conference = request.args.get('conference')
    #query for the selected teams
    if conference == None or conference == 'All':
        the_teams = all_teams
    elif conference in conferences:
        the_teams = models.team.query.join(models.year).filter(and_(models.team.conference==conference,models.year.year==current_year)).all()
    else:
        #the conference specified isn't valid
        return render_template('teams.html',conferences = conferences,no_data = True)

    #if no teams found
    if len(the_teams) < 1:
        return render_template('teams.html',conferences = conferences,no_data = True)

    #convert the data to list of lists
    key_list = ['espn_name','conference']
    hdrs = ['Team', 'Conference']

    return render_template('teams.html',
        title = 'Teams',
        hdrs = hdrs,
        data = the_teams,
        year = current_year,
        conferences = conferences,
        key_list = key_list,
        no_data = False)

@mod.route('/<the_year>/<the_team>')
@mod.route('/<the_year>/<the_team>/schedule')
def schedule(the_year,the_team):
    class tbl_game:
        def __init__(self):
            self.home_team = ''
            self.home_team_link = ''
            self.away_team = ''
            self.away_team_link = ''
            self.outcome = ''
            self.date = ''
            self.nuetral_site = False
        def __getitem__(self,key):
            return getattr(self,key)


    #get the ncaaID of the team, handle invalid team argument
    try:
        ncaaID = tf.get_team_param(the_team,'statsheet').ncaaID
    except AttributeError:
        #team wasn't found
        return render_template('schedules.html',no_data = True, team = the_team)

    #query for all the team's games for the year given
    gms = models.game.query.join(models.year).filter(and_(models.year.year==the_year,or_(models.game.home_team == ncaaID, models.game.away_team == ncaaID))).order_by(models.game.date).all()

    #if no games were found
    if len(gms) < 1:
        return render_template('schedules.html',no_data = True, team = the_team)
    #return str(gms)
    #condition the data
    the_games = []
    for gm in gms:
        this_g = tbl_game()
        for key,val in gm.__dict__.items():
            if key == 'home_team':
                try:
                    team_obj = models.team.query.filter(models.team.ncaaID==val).first()
                    if team_obj == None:
                        #no team found in db
                        this_g.home_team = str(val)
                        #no team link if not found in db
                        this_g.home_team_link = ''
                    else:
                        this_g.home_team = team_obj.ncaa
                        this_g.home_team_link = team_obj.statsheet
                except:
                    this_g.home_team = ''
                    this_g.home_team_link = ''
            elif key == 'away_team':
                try:
                    team_obj = models.team.query.filter(models.team.ncaaID==val).first()
                    if team_obj == None:
                        #no team found in db
                        this_g.away_team = str(val)
                        #no team link if not found in db
                        this_g.away_team_link = ''
                    else:
                        this_g.away_team = team_obj.ncaa
                        this_g.away_team_link = team_obj.statsheet
                except:
                    this_g.away_team = ''
                    this_g.away_team_link = ''
            elif 'outcome' in key:
                try:
                    if ncaaID != gm.home_team:
                        this_g.outcome = tf.win_loss_invert(gm.home_outcome)
                    else:
                        this_g.outcome = gm.home_outcome
                    #if the outcome is None, then raise an error to give an empty string
                    if this_g.outcome is None:
                        assert False
                except:
                    this_g.outcome = ''
            elif key == 'date':
                this_g.date = gm.date.strftime('%m-%d-%Y')

        this_g.neutral_site = gm.neutral_site
        the_games.append(this_g)

    key_list = ['date','home_team','away_team','outcome']
    hdrs = ['Date','Home Team','Away Team','Outcome']
    return render_template('schedules.html',
        title = 'Home',
        hdrs = hdrs,
        data = the_games,
        year = current_year,
        key_list = key_list,
        team = the_team,
        no_data = False)

@mod.route('/<the_year>/<the_team>/roster')
def roster(the_year,the_team):
    team_q = models.team.query.join(models.year).filter(and_(models.year.year==the_year,models.team.statsheet==the_team)).first()
    if team_q is None:
        #if no players are found, but team is valid
        return render_template('rosters.html',no_data = True,team = the_team)

    players = team_q.players
    plrs = []
    for p in players:
        plrs.append(p)

    if len(plrs) == 0:
        #if team isn't valid
        return redirect(url_for('teams.teams'))

    #convert the data to list of lists
    key_list = ['name','pclass','height','position']
    hdrs = ['Name', 'Class', 'Height','Position']

    return render_template('rosters.html',
        title = 'Roster',
        hdrs = hdrs,
        key_list = key_list,
        data = plrs,
        year = current_year,
        team = the_team,
        no_data = False)

@mod.route('/<the_year>/<the_team>/stats/points', methods=['GET','POST'])
@mod.route('/<the_year>/<the_team>/stats', methods=['GET','POST'])
def points(the_year, the_team):
    a = time.time()
    team_obj = tf.get_team_param(the_team,'statsheet')
    if team_obj == None:
        return render_template('team_points.html',no_data = True,team = the_team)

    filter_fields = ['location','outcome']
    if request.method == 'POST':
        q = models.pbp_stat.query.join(models.game).filter(or_(models.game.away_team == team_obj.ncaaID, models.game.home_team == team_obj.ncaaID))
        q = df.process_filter(filter_fields, request.form, q, team_obj = team_obj)
        pbp_data = q.all()
    else:
        #get the box and play by play data
        #a = datetime.now()
        x = time.time()
        pbp_data = models.pbp_stat.query.join(models.game).filter(or_(models.game.away_team == team_obj.ncaaID, models.game.home_team == team_obj.ncaaID)).all()
        y = time.time()
        #q = models.pbp_stat.query.join(models.game).filter(or_(models.game.away_team == team_obj.ncaaID, models.game.home_team == team_obj.ncaaID))
        #q = q.filter(or_(and_(models.game.home_team==team_obj.ncaaID,models.pbp_stat.teamID==0),and_(models.game.away_team==team_obj.ncaaID,models.pbp_stat.teamID==1)))
        q = db.session.query(func.sum(models.pbp_stat.home_score).label("max_score"))
        l = []
        for r in q.all():
            l.append(r)
        #return str(l)
        z = time.time()
        #pbp_data = models.pbp_stat.query.with_entities(models.pbp_stat.worth,models.pbp_stat.time,models.pbp_stat.time,models.pbp_stat.possession_time,models.pbp_stat.possession_time_adj).join(models.game)
        #pbp_data.filter(or_(models.game.away_team == team_obj.ncaaID, models.game.home_team == team_obj.ncaaID)).all()
        q = tf.query_by_year('pbp_stat',current_year,'game')
        q = q.filter(or_(models.game.away_team == team_obj.ncaaID, models.game.home_team == team_obj.ncaaID))

    if len(pbp_data) == 0:
        return render_template('team_points.html',no_data = True,team = the_team)

    #set defaults
    default_color = 'blue'
    opp_default_color = 'red'

    a = time.time()
    poss_chart_home, time_diff = poss_time_chart(pbp_data,team_obj,chartid='home_poss',chart_color=default_color)
    b = time.time()
    poss_chart_away,time_diff = poss_time_chart(pbp_data,team_obj,opp_team=True,chartid='away_poss',chart_color=opp_default_color)
    c = time.time()
    diff_chart = scoring_diff_chart(pbp_data,team_obj,chartid='diff',chart_color=default_color)
    d = time.time()
    shot_chart,time_diff = shot_type_chart(pbp_data,team_obj,chartid='shot_type',chart_color=default_color)
    e = time.time()
    #return str([b-a,c-b,d-c,e-d, y-x, z-y])

    #unique html chart ids
    chart_ids = df.make_dict(diff_chart = diff_chart.chartid, poss_chart_home = poss_chart_home.chartid,
        poss_chart_away = poss_chart_away.chartid,shot_chart = shot_chart.chartid)

    #construct a dict to hold all the charts
    column_charts = [diff_chart, poss_chart_home,poss_chart_away]
    line_charts = []
    pie_diff_charts = [shot_chart]


    t = a-b
    #return str(t)
    return render_template(
        'team_points.html',
        column_charts = column_charts,
        line_charts = line_charts,
        pie_diff_charts = pie_diff_charts,
        chart_ids = chart_ids,
        no_data = False,
        team = the_team,
        year = the_year,
        locations = ['All','Home','Away'],
        outcomes = ['All','Wins','Losses'])
def shot_type_chart(data,team_obj,chartid='',chart_color='blue'):
    the_dict_team = dict((k,{'val' : 0}) for k in [shot+'s' for shot in df.shot_list()])
    the_dict_opp = dict((k,{'val' : 0}) for k in [shot+'s' for shot in df.shot_list()])

    '''q = models.pbp_stat.query.join(models.game).filter(or_(models.game.away_team == team_obj.ncaaID, models.game.home_team == team_obj.ncaaID))

    q_opp = q.filter(or_(and_(models.game.home_team==team_obj.ncaaID,models.pbp_stat.teamID==0),and_(models.game.away_team==team_obj.ncaaID,models.pbp_stat.teamID==1)))
    q_team = q.filter(or_(and_(models.game.home_team==team_obj.ncaaID,models.pbp_stat.teamID==1),and_(models.game.away_team==team_obj.ncaaID,models.pbp_stat.teamID==0)))
    q_opp = q_opp.filter(models.pbp_stat.stat_type == 'POINT')
    q_team = q_team.filter(models.pbp_stat.stat_type == 'POINT')

    a = datetime.now()
    for st in q_team:
        shot_type = df.shot_type_convert(st.point_type)+'s'
        try:
            the_dict_team[shot_type]['val'] += int(st.worth)
        except:
            continue
    b = datetime.now()
    for st in q_opp:
        shot_type = df.shot_type_convert(st.point_type)+'s'
        try:
            the_dict_opp[shot_type]['val'] += int(st.worth)
        except:
            continue'''
    b = datetime.now()
    for st in data:
        shot_type = df.shot_type_convert(st.point_type)+'s'
        try:
            if is_team(st,team_obj):
                the_dict_team[shot_type]['val'] += int(st.worth)
            else:
                the_dict_opp[shot_type]['val'] += int(st.worth)
        except:
            continue
    c = datetime.now()

    #shot type pie chart
    this_chart = cf.google_chart(chart_type='pie_diff',chartid=chartid)
    this_chart.js_options()

    this_chart.data = [['Shot Type','Shots',{ 'role': 'tooltip','p': {'html': 'true'} }]]
    this_chart.data2 = [['Shot Type','Shots',{ 'role': 'tooltip','p': {'html': 'true'} }]]
    tooltip = '<div>test</div>'
    for key in the_dict_team.keys():
        this_chart.data.append([str(key),the_dict_team[key]['val'],tooltip])
    for key in the_dict_opp.keys():
        this_chart.data2.append([str(key),the_dict_opp[key]['val'],tooltip])

    time_diff1 = b-c
    time_diff2 = c-c
    return this_chart,[time_diff1.microseconds,time_diff2.microseconds]
def poss_time_chart(data,team_obj,opp_team=False,chartid='',chart_color='blue'):
    max_possession_time = 40
    possession_time_interval = 5
    chart_series = 'Opponent'
    a = datetime.now()
    the_dict = dict((k, {'val': 0, 'poss': 0,'color': 'blue'}) for k in range(max_possession_time)[0::possession_time_interval])
    '''if opp_team:
        chart_series = 'Opponent'
        q = q.filter(or_(and_(models.game.home_team==team_obj.ncaaID,models.pbp_stat.teamID==0),and_(models.game.away_team==team_obj.ncaaID,models.pbp_stat.teamID==1)))
    else:
        chart_series = str(team_obj.ncaa)
        q = q.filter(or_(and_(models.game.home_team==team_obj.ncaaID,models.pbp_stat.teamID==1),and_(models.game.away_team==team_obj.ncaaID,models.pbp_stat.teamID==0)))
    #b = datetime.now()

    q_points = q.filter(models.pbp_stat.worth > 0)
    for st in q_points:
        try:
            poss_time_bin = int(df.myround(st.possession_time_adj,possession_time_interval))
            the_dict[poss_time_bin]['val'] += int(st.worth)
        except:
            continue
    q_poss = q.filter(models.pbp_stat.possession_time > -1)
    for st in q_poss:#
        try:
            poss_time_bin = int(df.myround(st.possession_time_adj,possession_time_interval))
            the_dict[poss_time_bin]['poss'] += 1
        except:
            continue'''
    for st in data:
        try:
            if (is_team(st,team_obj) and not opp_team) or (not is_team(st,team_obj) and opp_team):
                continue
            poss_time_bin = int(df.myround(st.possession_time_adj,possession_time_interval))
            if st.worth > 0:
                the_dict[poss_time_bin]['val'] += int(st.worth)
            elif st.possession_time > -1:
                the_dict[poss_time_bin]['poss'] += 1
        except:
            continue


    b = datetime.now()

    #home team scoring by possession time chart
    this_chart = cf.google_chart(chart_type='column',chartid=chartid)
    this_chart.options['hAxis']['title'] = 'Possession Time (sec)'
    this_chart.options['vAxis']['title'] = 'Points'
    this_chart.options['colors'] = [chart_color]
    this_chart.formatters = [['0.00',1]]
    this_chart.js_options()
    this_chart.data, poss_home_max_val = df.time_hist_to_google_data(the_dict,['Possession Time',chart_series],5,divide_by='poss')

    time_diff = b - a
    return this_chart, time_diff.microseconds
def scoring_diff_chart(data,team_obj,chartid='',chart_color='blue'):
    chart_series = 'Scoring Differential'

    '''q_opp = q.filter(or_(and_(models.game.home_team==team_obj.ncaaID,models.pbp_stat.teamID==0),and_(models.game.away_team==team_obj.ncaaID,models.pbp_stat.teamID==1)))
    q_team = q.filter(or_(and_(models.game.home_team==team_obj.ncaaID,models.pbp_stat.teamID==1),and_(models.game.away_team==team_obj.ncaaID,models.pbp_stat.teamID==0)))
    q_opp = q_opp.filter(models.pbp_stat.worth > 0)
    q_team = q_team.filter(models.pbp_stat.worth > 0)'''

    game_time_interval = 5
    the_dict = dict((k,{'val':0,'color':chart_color}) for k in range(40+game_time_interval)[0::game_time_interval])
    for st in data:
        try:
            game_time_bin = df.myround(st.time, game_time_interval)
            if is_team(st,team_obj):
                the_dict[game_time_bin]['val'] += int(st.worth)
            else:
                the_dict[game_time_bin]['val'] -= int(st.worth)
        except:
            continue

    #scoring difference chart
    this_chart = cf.google_chart(chart_type='column',chartid=chartid)
    this_chart.options['hAxis']['title'] = 'Game Time (min)'
    this_chart.options['vAxis']['title'] = 'Points'
    this_chart.options['colors'] = [chart_color]
    this_chart.formatters = [['0',1]]
    this_chart.js_options()
    this_chart.data, diff_max_val = df.time_hist_to_google_data(the_dict,['Possession Time',chart_series],game_time_interval)

    return this_chart
def is_team(st,team):
    return not ((st.game.home_team==team.ncaaID and st.teamID==0) or (st.game.away_team==team.ncaaID and st.teamID==1))
def possession_points_hist(the_dict,stat,bin):
    temp = the_dict
    try:
        if stat.possession_time > -1:
            the_dict[bin]['poss'] += 1
        if stat.worth > 0:
            the_dict[bin]['val'] += stat.worth
        return the_dict
    except:
        return temp

