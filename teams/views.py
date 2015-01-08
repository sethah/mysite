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
    all_teams = models.team.query.all()

    #get list of unique conferences
    conferences = ['All']+sorted(list(set([tm.conference for tm in all_teams])))

    conference = request.args.get('conference')
    #query for the selected teams
    if conference == None or conference == 'All':
        the_teams = all_teams
    elif conference in conferences:
        the_teams = models.team.query.filter(models.team.conference==conference).all()
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
        conferences = conferences,
        key_list = key_list,
        no_data = False)

@mod.route('/<the_team>', methods=['GET','POST'])
@mod.route('/<the_team>/schedule', methods=['GET','POST'])
def schedule(the_team):
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

    #handle post request
    if request.method == 'POST':
        the_year = int(request.form['year'])
    else:
        the_year = df.get_year()
    date_range = df.date_range(the_year)

    #check if team is in db
    team_obj = models.team.query.filter(models.team.statsheet==the_team).first()
    if the_team == None:
        return render_template('schedules.html',no_data = True, team = the_team)

    #get filter values
    q = models.game.query.with_entities(models.game.date).all()
    years = []
    for date in q:
        if df.get_year_from_date(date.date) not in years:
            years.append(date.date.year)

    #query for all the team's games for the year given
    gms = models.game.query.filter(and_(models.game.date.between(date_range[0],date_range[1]),or_(models.game.home_team == team_obj.ncaaID, models.game.away_team == team_obj.ncaaID))).order_by(models.game.date).all()

    #if no games were found
    if len(gms) < 1:
        return render_template('schedules.html',no_data = True, team = the_team)

    #condition the data
    the_games = []
    for gm in gms:
        this_g = tbl_game()
        this_g.home_team, this_g.home_team_link = schedule_team_link(gm.home_team)
        this_g.away_team, this_g.away_team_link = schedule_team_link(gm.away_team)
        this_g.outcome = schedule_outcome(gm,team_obj.ncaaID)
        this_g.date = gm.date.strftime('%m-%d-%Y')
        this_g.neutral_site = gm.neutral_site
        the_games.append(this_g)

    key_list = ['date','home_team','away_team','outcome']
    hdrs = ['Date','Home Team','Away Team','Outcome']
    return render_template('schedules.html',
        title = team_obj.espn_name,
        hdrs = hdrs,
        data = the_games,
        year = the_year,
        key_list = key_list,
        years = years,
        team = the_team,
        no_data = False)
def schedule_outcome(game,teamID):
    if game.home_team != teamID:
        outcome = tf.win_loss_invert(game.home_outcome)
    else:
        outcome = game.home_outcome
    return df.xstr(outcome)
def schedule_team_link(teamID):
    try:
        team_obj = models.team.query.filter(models.team.ncaaID==teamID).first()
        if team_obj == None:
            #no team found in db
            team = str(teamID)
            #no team link if not found in db
            link_slug = ''
        else:
            team = team_obj.ncaa
            link_slug = team_obj.statsheet
    except:
        team = ''
        link_slug = ''
    return df.xstr(team), df.xstr(link_slug)
@mod.route('/<the_team>/roster', methods=['GET','POST'])
def roster(the_team):
    if request.method == 'POST':
        the_year = int(request.form['year'])
    else:
        #default to current year
        the_year = df.get_year()

    #check if team is in db
    team_obj = models.team.query.filter(models.team.statsheet==the_team).first()
    if the_team == None:
        return render_template('rosters.html',no_data = True, team = the_team)

    #get filter values
    q = models.player.query.join(models.team).filter(models.team.statsheet==the_team).all()
    years = []
    for plr in q:
        if plr.year not in years:
            years.append(plr.year)

    #TODO: handle invalid teams?
    players = models.player.query.join(models.team).filter(and_(models.player.year==the_year,models.team.statsheet==the_team)).all()
    if players is None:
        #if no players are found, but team is valid
        return render_template('rosters.html',no_data = True,team = the_team)

    plrs = [p for p in players]
    if len(plrs) == 0:
        #if team isn't valid
        return redirect(url_for('teams.teams'))

    #convert the data to list of lists
    key_list = ['name','pclass','height','position']
    hdrs = ['Name', 'Class', 'Height','Position']

    return render_template('rosters.html',
        title = team_obj.espn_name+' Roster',
        hdrs = hdrs,
        key_list = key_list,
        data = plrs,
        year = the_year,
        years = years,
        team = the_team,
        no_data = False)

@mod.route('/<the_team>/stats/points', methods=['GET','POST'])
@mod.route('/<the_team>/stats', methods=['GET','POST'])
def points(the_team):
    the_year = df.get_year()
    a = time.time()
    team_obj = tf.get_team_param(the_team,'statsheet')
    if team_obj == None:
        return render_template('team_points.html',no_data = True,team = the_team)

    filter_fields = [
                    ['location',['All','Home','Away']],
                    ['outcome',['All','Wins','Losses']]
                    ]
    filter_dict = {}
    for field in filter_fields:
        filter_dict[field[0]] = dict((field[1][j],{'val':'','selected':False}) for j in range(len(field[1])))

    for field in request.form.keys():
        try:
            filter_dict[field][request.form[field]]['selected'] = True
        except:
            continue

    if request.method == 'POST' and request.form.keys() != []:
        the_form = request.form
        q = models.pbp_stat.query
    else:
        the_form = None
        q = models.pbp_stat.query
        pass

    #set defaults
    default_color = 'blue'
    opp_default_color = 'red'

    poss_chart_home  = poss_time_chart(q,team_obj,chartid='home_poss',chart_color=default_color,form=the_form)
    poss_chart_away = poss_time_chart(q,team_obj,opp_team=True,chartid='away_poss',chart_color=opp_default_color,form=the_form)
    diff_chart = scoring_diff_chart(q,team_obj,chartid='diff',chart_color=default_color,form=the_form)
    shot_chart = shot_type_chart(q,team_obj,chartid='shot_type',chart_color=default_color,form=the_form)

    #unique html chart ids
    chart_ids = df.make_dict(diff_chart = diff_chart.chartid, poss_chart_home = poss_chart_home.chartid,
        poss_chart_away = poss_chart_away.chartid,shot_chart = shot_chart.chartid)

    #construct a dict to hold all the charts
    column_charts = [diff_chart, poss_chart_home,poss_chart_away]
    line_charts = []
    pie_diff_charts = [shot_chart]

    return render_template(
        'team_points.html',
        title=team_obj.espn_name+' Points',
        column_charts = column_charts,
        line_charts = line_charts,
        pie_diff_charts = pie_diff_charts,
        chart_ids = chart_ids,
        no_data = False,
        team = the_team,
        year = the_year,
        filters = filter_dict)
def shot_type_chart(q,team_obj,chartid='',chart_color='blue',form=None):
    the_dict_team = dict((k,{'val' : 0}) for k in [shot+'s' for shot in df.shot_list()])
    the_dict_opp = dict((k,{'val' : 0}) for k in [shot+'s' for shot in df.shot_list()])

    q = q.with_entities(models.pbp_stat.point_type, models.pbp_stat.worth).filter(models.pbp_stat.stat_type == 'POINT')
    q = q.join(models.game).filter(or_(models.game.away_team == team_obj.ncaaID, models.game.home_team == team_obj.ncaaID))
    if form != None:
        q = tf.process_filter(form,q,team_obj=team_obj)
        pass
    q_team = q.filter(or_(and_(models.game.home_team==team_obj.ncaaID,models.pbp_stat.teamID==1),and_(models.game.away_team==team_obj.ncaaID,models.pbp_stat.teamID==0)))
    q_opp = q.filter(or_(and_(models.game.home_team==team_obj.ncaaID,models.pbp_stat.teamID==0),and_(models.game.away_team==team_obj.ncaaID,models.pbp_stat.teamID==1)))

    for st in q_team.all():
        shot_type = df.shot_type_convert(st.point_type)+'s'
        try:
            the_dict_team[shot_type]['val'] += int(st.worth)
        except:
            continue
    for st in q_opp.all():
        shot_type = df.shot_type_convert(st.point_type)+'s'
        try:
            the_dict_opp[shot_type]['val'] += int(st.worth)
        except:
            continue

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

    return this_chart
def poss_time_chart(q,team_obj,opp_team=False,chartid='',chart_color='blue',form=None):
    max_possession_time = 40
    possession_time_interval = 5
    chart_series = 'Opponent'

    #filter for games that have this team
    q = q.with_entities(models.pbp_stat.worth,  models.pbp_stat.possession_time, models.pbp_stat.possession_time_adj)
    q = q.join(models.game).filter(or_(models.game.away_team == team_obj.ncaaID, models.game.home_team == team_obj.ncaaID))
    if form != None:
        q = tf.process_filter(form,q,team_obj=team_obj)

    the_dict = dict((k, {'val': 0, 'poss': 0,'color': 'blue'}) for k in range(max_possession_time)[0::possession_time_interval])
    if opp_team:
        chart_series = 'Opponent'
        q = q.filter(or_(and_(models.game.home_team==team_obj.ncaaID,models.pbp_stat.teamID==0),and_(models.game.away_team==team_obj.ncaaID,models.pbp_stat.teamID==1)))
    else:
        chart_series = str(team_obj.ncaa)
        q = q.filter(or_(and_(models.game.home_team==team_obj.ncaaID,models.pbp_stat.teamID==1),and_(models.game.away_team==team_obj.ncaaID,models.pbp_stat.teamID==0)))

    q_points = q.filter(models.pbp_stat.worth > 0)
    for st in q_points:
        try:
            poss_time_bin = int(df.myround(st.possession_time_adj,possession_time_interval))
            the_dict[poss_time_bin]['val'] += int(st.worth)
        except:
            continue
    q_poss = q.filter(models.pbp_stat.possession_time > -1)
    for st in q_poss:
        try:
            poss_time_bin = int(df.myround(st.possession_time_adj,possession_time_interval))
            the_dict[poss_time_bin]['poss'] += 1
        except:
            continue

    #home team scoring by possession time chart
    this_chart = cf.google_chart(chart_type='column',chartid=chartid)
    this_chart.options['hAxis']['title'] = 'Possession Time (sec)'
    this_chart.options['vAxis']['title'] = 'Points'
    this_chart.options['colors'] = [chart_color]
    this_chart.formatters = [['0.00',1]]
    this_chart.js_options()
    this_chart.data, poss_home_max_val = df.time_hist_to_google_data(the_dict,['Possession Time',chart_series],5,divide_by='poss')

    return this_chart
def scoring_diff_chart(q,team_obj,chartid='',chart_color='blue',form=None):
    chart_series = 'Scoring Differential'

    q = q.with_entities(models.pbp_stat.worth,  models.pbp_stat.time, models.game.home_team, models.game.away_team, models.game.home_outcome)
    q = q.join(models.game).filter(or_(models.game.away_team == team_obj.ncaaID, models.game.home_team == team_obj.ncaaID))
    if form != None:
        q = tf.process_filter(form,q,team_obj=team_obj)

    q_opp = q.filter(or_(and_(models.game.home_team==team_obj.ncaaID,models.pbp_stat.teamID==0),and_(models.game.away_team==team_obj.ncaaID,models.pbp_stat.teamID==1)))
    q_team = q.filter(or_(and_(models.game.home_team==team_obj.ncaaID,models.pbp_stat.teamID==1),and_(models.game.away_team==team_obj.ncaaID,models.pbp_stat.teamID==0)))
    q_opp = q_opp.filter(models.pbp_stat.worth > 0)
    q_team = q_team.filter(models.pbp_stat.worth > 0)

    game_time_interval = 5
    the_dict = dict((k,{'val':0,'color':chart_color}) for k in range(40+game_time_interval)[0::game_time_interval])
    for st in q_team.all():
        try:
            game_time_bin = df.myround(st.time, game_time_interval,game_time=True)
            the_dict[game_time_bin]['val'] += int(st.worth)
        except:
            continue
    for st in q_opp.all():
        try:
            game_time_bin = df.myround(st.time, game_time_interval,game_time=True)
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

