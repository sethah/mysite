from flask import render_template, flash, redirect, session, url_for, request, g, send_file, Blueprint
from forms import LoginForm
from mysite import models
import chart_functions as cf
import error_functions as ef
import data_functions as df
import team_info_functions as tf
from sqlalchemy import and_, or_
from datetime import datetime
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
def points(the_team):
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
        pbp_data = models.pbp_stat.query.join(models.game).filter(or_(models.game.away_team == team_obj.ncaaID, models.game.home_team == team_obj.ncaaID)).all()

    if len(pbp_data) == 0:
        return render_template('team_points.html',no_data = True,team = the_team)

    #set defaults
    default_color = 'blue'
    opp_default_color = 'red'

    #game time args
    game_time_interval = 5
    game_end_time = int(df.myround(pbp_data[-1].time,5,'up'))
    game_time_keys = range(45)[0::game_time_interval]

    #possession time args
    poss_time_interval = 5
    max_possession_time = 40
    poss_time_keys = range(max_possession_time)[0::game_time_interval]


    #create dicts to hold data
    diff_dict = {}
    poss_time_dict = {}
    shot_type_dict = {}
    for key in game_time_keys:
        diff_dict[key] = {'val':0,'color':default_color}

    tms = ['opp','team']
    #create possession time dicts
    for tm in tms:
        poss_time_dict[tm] = {}
        shot_type_dict[tm] = {}
        for shot in df.shot_list():
            shot_type_dict[tm][shot+'s'] = {'val': 0}
        if tm == 'team':
            color = default_color
        else:
            color = opp_default_color
        for key in poss_time_keys:
            poss_time_dict[tm][key] = {'val':0,'poss':0,'color':color}


    #loop through the data only once
    for st in pbp_data:
        cur_team = df.current_team(st.teamID,team_obj.ncaaID,st.game.home_team,st.game.away_team)
        if cur_team == None:
            continue

        #find the appropriate bins for this data point
        game_time_bin = df.myround(st.time, game_time_interval)
        poss_time_bin = df.myround(st.possession_time_adj,poss_time_interval)

        #track possessions
        if poss_time_bin <= max_possession_time-poss_time_interval:
            if st.possession_time > -1:
                poss_time_dict[cur_team][poss_time_bin]['poss'] += 1
            if st.worth > 0:
                poss_time_dict[cur_team][poss_time_bin]['val'] += st.worth
        #differential score
        if st.worth > 0:
            if cur_team == 'team':
                #home team scored
                diff_dict[game_time_bin]['val'] += st.worth
            else:
                #away team scored
                diff_dict[game_time_bin]['val'] -= st.worth
        #shot type
        if st.stat_type == 'POINT':
            shot_type = df.shot_type_convert(st.point_type)+'s'
            try:
                shot_type_dict[cur_team][shot_type]['val'] += st.worth
            except:
                continue

    #make the chart dictionaries
    diff_chart = df.make_dict(id='chart-div diff',data=[],options='')
    poss_chart_home = df.make_dict(id='chart-div home_poss',data=[],options='')
    poss_chart_away = df.make_dict(id='chart-div away_poss',data=[],options='')
    shot_type_chart = df.make_dict(data1 = [],data2 = [],id='chart-div shot_type',options='')
    #shot_type_away = df.make_dict(data = [],id='chart-div shot_type',options='')

    #convert dictionary to list of lists for google charts
    diff_chart['data'], diff_max_val = df.time_hist_to_google_data(diff_dict,['Possession Time','Scoring Differential'],game_time_interval)
    poss_chart_home['data'], poss_home_max_val = df.time_hist_to_google_data(poss_time_dict['team'],['Possession Time','team'],poss_time_interval,divide_by='poss')
    poss_chart_away['data'], poss_away_max_val = df.time_hist_to_google_data(poss_time_dict['opp'],['Possession Time','opp'],poss_time_interval,divide_by='poss')
    #return str(poss_chart_home['data'])
    shot_type_chart['data1'] = [['Shot Type','Shots',{ 'role': 'tooltip','p': {'html': 'true'} }]]
    shot_type_chart['data2'] = [['Shot Type','Shots',{ 'role': 'tooltip','p': {'html': 'true'} }]]
    tooltip = '<div>test</div>'
    for key in shot_type_dict['team'].keys():
        shot_type_chart['data1'].append([str(key),shot_type_dict['team'][key]['val'],tooltip])
    for key in shot_type_dict['opp'].keys():
        shot_type_chart['data2'].append([str(key),shot_type_dict['opp'][key]['val'],tooltip])


    if poss_home_max_val > poss_away_max_val:
        poss_max_val = poss_home_max_val
    else: poss_max_val = poss_away_max_val

    #common column chart options
    hAxis = {'slantedText':"true",'slantedTextAngle':'45'}
    column_options = cf.chart_options2('column',new_options = {'hAxis':hAxis})

    #common line chart options
    line_options = cf.chart_options2('line')

    #common pie chart options
    pie_options = cf.chart_options2('pie')

    #scoring difference chart
    hAxis = {'title':'Game Time (min)'}
    vAxis = {'title':'Points'}
    diff_options = cf.chart_options2('',options = column_options,new_options = {'hAxis':hAxis, 'vAxis':vAxis, 'colors':[default_color]})
    diff_chart['options'] = json.dumps(diff_options)

    #home team scoring by possession time chart
    hAxis = {'title':'Possession Time (sec)'}
    vAxis = {'title':'Points','maxValue':str(poss_max_val),'minValue':'0'}
    poss_home_options = cf.chart_options2('',options = column_options,new_options = {'hAxis':hAxis,'vAxis':vAxis,'colors':[default_color]})
    poss_chart_home['options'] = json.dumps(poss_home_options)

    #away team scoring by possession time chart
    hAxis = {'title':'Possession Time (sec)'}
    vAxis = {'title':'Points','maxValue':str(poss_max_val),'minValue':'0'}
    poss_away_options = cf.chart_options2('',options = column_options,new_options = {'hAxis':hAxis,'vAxis':vAxis,'colors':[opp_default_color]})
    poss_chart_away['options'] = json.dumps(poss_away_options)

    #home team shot types
    #hAxis = {'maxValue':'5:00','minValue':'00:00','title':'Game Time (min)'}
    shot_type_options = cf.chart_options2('',options = pie_options, new_options = {})
    shot_type_chart['options'] = json.dumps(shot_type_options)

    #unique html chart ids
    chart_ids = df.make_dict(diff_chart = diff_chart['id'], poss_chart_home = poss_chart_home['id'], poss_chart_away = poss_chart_away['id'],
        shot_type_chart = shot_type_chart['id'])

    #set misc chart options
    diff_chart['formatters'] = [['0',1]]
    poss_chart_home['formatters'] = [['0.00',1]]
    poss_chart_away['formatters'] = [['0.00',1]]

    #construct a dict to hold all the charts
    column_charts = [diff_chart, poss_chart_home,poss_chart_away]
    line_charts = []
    pie_diff_charts = [shot_type_chart]

    return render_template(
        'team_points.html',
        column_charts = column_charts,
        line_charts = line_charts,
        pie_diff_charts = pie_diff_charts,
        chart_ids = chart_ids,
        no_data = False,
        team = the_team,
        locations = ['All','Home','Away'],
        outcomes = ['All','Wins','Losses'])

