from flask import Blueprint, render_template, flash, redirect, url_for
from mysite import models
import team_info_functions as tf
import error_functions as ef
import data_functions as df
import game.game_functions as gf
from sqlalchemy import and_, or_
from datetime import datetime
import chart_functions as cf
import json


mod = Blueprint('game', __name__, url_prefix='/game')

@mod.route('/<the_month>/<the_day>/<the_year>/<game_string>/box_stats')
def box_stats(the_month, the_day, the_year, game_string):
    #get all the game data and handle errors
    home_team_obj, away_team_obj, date = gf.init_game_data(the_month,the_day,the_year,game_string)

    if date == None:
        #the url is bad
        return redirect(url_for('main.index'))

    box_data = models.box_stat.query.join(models.game).filter(and_(models.game.date == date, models.game.home_team == home_team_obj.ncaaID)).all()
    home_roster = models.player.query.join(models.team).filter(models.team.statsheet==home_team_obj.statsheet).all()
    away_roster = models.player.query.join(models.team).filter(models.team.statsheet==away_team_obj.statsheet).all()
    away_roster = [p.name for p in away_roster]
    home_roster = [p.name for p in home_roster]

    #return str(box_data)
    if len(box_data) == 0:
        return render_template('game_scoring.html',no_game = True)

    home_team_box = models.box_stat()
    away_team_box = models.box_stat()
    away_data = []
    home_data = []
    for bst in box_data:
        #remove the nones from each stat
        for key,val in bst.__dict__.items():
            if getattr(bst,key) == None:
                setattr(bst,key,0)
        if bst.name == home_team_obj.statsheet:
            home_team_box = bst
            try:
                setattr(home_team_box,'name',tf.get_team_param(home_team_box.name,'statsheet').espn_name)
            except: pass
        elif bst.name == away_team_obj.statsheet:
            away_team_box = bst
            try:
                setattr(away_team_box,'name',tf.get_team_param(away_team_box.name,'statsheet').espn_name)
            except: pass
        elif bst.name != None and bst.name != 0:
            if bst.name in home_roster:
                home_data.append(bst)
            elif bst.name in away_roster:
                away_data.append(bst)
            elif len(home_roster) > 0 and len(away_roster) == 0:
                away_data.append(bst)
            elif len(away_roster) > 0 and len(home_roster) == 0:
                home_data.append(bst)



    #convert the data to list of lists
    key_list = ['name','min','fgm','tpm','ftm','pts','reb','oreb','dreb','ast','stl','blk','pf']
    hdrs = ['Player','MIN','FGM','3PM','FTM','PTS','REB','OREB','DREB','AST','STL','BLK','PF']

    return render_template('box_stats.html',
        title = 'Home',
        hdrs = hdrs,
        key_list = key_list,
        home_data = home_data,
        away_data = away_data,
        home_team_obj = home_team_obj,
        away_team_obj = away_team_obj,
        home_roster = home_roster,
        home_team_box = home_team_box,
        away_team_box = away_team_box,
        the_month = the_month,
        the_day = the_day,
        the_year = the_year,
        game_string = game_string)

@mod.route('/<the_month>/<the_day>/<the_year>/<game_string>/scoring')
def game_scoring(the_month, the_day, the_year, game_string):

    #get all the game data
    home_team_obj, away_team_obj, date = gf.init_game_data(the_month,the_day,the_year,game_string)

    if date == None:
        #the url is bad
        return redirect(url_for('main.index'))

    home_team = str(home_team_obj.espn_name)
    away_team = str(away_team_obj.espn_name)
    tms = [away_team,home_team]

    #get the box and play by play data
    pbp_data = models.pbp_stat.query.join(models.game).filter(and_(models.game.date == date, models.game.home_team == home_team_obj.ncaaID)).all()

    if len(pbp_data) == 0:
        return render_template('game_scoring.html',no_game = True,the_month = the_month,the_day = the_day,the_year = the_year,game_string = game_string)

    #set defaults
    default_color = 'blue'
    away_default_color = 'red'

    #game time args
    game_time_interval = 5
    game_end_time = int(df.myround(pbp_data[-1].time,5,'up'))
    game_time_keys = range(game_end_time)[0::game_time_interval]

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

    #create possession time dicts
    for tm in tms:
        poss_time_dict[tm] = {}
        shot_type_dict[tm] = {}
        for shot in df.shot_list():
            shot_type_dict[tm][shot+'s'] = {'val': 0}
        if tm == home_team:
            color = default_color
        else:
            color = away_default_color
        for key in poss_time_keys:
            poss_time_dict[tm][key] = {'val':0,'poss':0,'color':color}

    #initialize some stuff
    score_time_data = [['Time',{ 'role': 'tooltip','p': {'html': 'true'} }, home_team,away_team]]

    #loop through the data only once
    for st in pbp_data:
        #add new data points only if the time has changed
        tooltip = '<div style="padding:5px 5px 5px 5px;"><div>'+str(st.home_score)+'-'+str(st.away_score)+'</div><div>'+str(cf.game_time_to_datetime(st.time))+'</div>'
        score_triple = [st.time,tooltip,st.home_score,st.away_score]
        if score_triple not in score_time_data:
            score_time_data.append(score_triple)

        #find the appropriate bins for this data point
        game_time_bin = df.myround(st.time, game_time_interval)
        poss_time_bin = df.myround(st.possession_time_adj,poss_time_interval)

        #track possessions
        if poss_time_bin <= max_possession_time-poss_time_interval:
            if st.possession_time > -1:
                poss_time_dict[tms[st.teamID]][poss_time_bin]['poss'] += 1
            if st.worth > 0:
                poss_time_dict[tms[st.teamID]][poss_time_bin]['val'] += st.worth
        #differential score
        if st.worth > 0:
            if st.teamID == 1:
                #home team scored
                diff_dict[game_time_bin]['val'] += st.worth
            else:
                #away team scored
                diff_dict[game_time_bin]['val'] -= st.worth
        #shot type
        if st.stat_type == 'POINT':
            shot_type = df.shot_type_convert(st.point_type)+'s'
            try:
                shot_type_dict[tms[st.teamID]][shot_type]['val'] += st.worth
            except:
                continue

    #make the chart dictionaries
    diff_chart = df.make_dict(id='chart-div diff',data=[],options='')
    poss_chart_home = df.make_dict(id='chart-div home_poss',data=[],options='')
    poss_chart_away = df.make_dict(id='chart-div away_poss',data=[],options='')
    score_time_chart = df.make_dict(data = score_time_data,id='chart-div score_time',options='')
    shot_type_chart = df.make_dict(data1 = [],data2 = [],id='chart-div shot_type',options='')
    #shot_type_away = df.make_dict(data = [],id='chart-div shot_type',options='')

    #convert dictionary to list of lists for google charts
    diff_chart['data'], diff_max_val = df.time_hist_to_google_data(diff_dict,['Possession Time','Scoring Differential'],game_time_interval)
    poss_chart_home['data'], poss_home_max_val = df.time_hist_to_google_data(poss_time_dict[home_team],['Possession Time',home_team],poss_time_interval,divide_by='poss')
    poss_chart_away['data'], poss_away_max_val = df.time_hist_to_google_data(poss_time_dict[away_team],['Possession Time',away_team],poss_time_interval,divide_by='poss')
    #return str(poss_chart_home['data'])
    shot_type_chart['data1'] = [['Shot Type','Shots',{ 'role': 'tooltip','p': {'html': 'true'} }]]
    shot_type_chart['data2'] = [['Shot Type','Shots',{ 'role': 'tooltip','p': {'html': 'true'} }]]
    tooltip = '<div>test</div>'
    for key in shot_type_dict[home_team].keys():
        shot_type_chart['data1'].append([str(key),shot_type_dict[home_team][key]['val'],tooltip])
    for key in shot_type_dict[away_team].keys():
        shot_type_chart['data2'].append([str(key),shot_type_dict[away_team][key]['val'],tooltip])


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
    poss_away_options = cf.chart_options2('',options = column_options,new_options = {'hAxis':hAxis,'vAxis':vAxis,'colors':[away_default_color]})
    poss_chart_away['options'] = json.dumps(poss_away_options)

    #team scoring by game time
    hAxis = {'maxValue':str(game_end_time),'minValue':'0','title':'Game Time (min)'}
    score_time_options = cf.chart_options2('',options = line_options, new_options = {'hAxis':hAxis,'vAxis':vAxis, 'colors':[default_color,away_default_color]})
    score_time_chart['options'] = json.dumps(score_time_options)

    #home team shot types
    #hAxis = {'maxValue':'5:00','minValue':'00:00','title':'Game Time (min)'}
    shot_type_options = cf.chart_options2('',options = pie_options, new_options = {})
    shot_type_chart['options'] = json.dumps(shot_type_options)

    #away team shot types
    #hAxis = {'maxValue':'5:00','minValue':'00:00','title':'Game Time (min)'}
    #score_time_options = cf.chart_options2(options = line_options, new_options = {'hAxis':hAxis,'vAxis':vAxis, 'colors':[default_color,away_default_color]})
    #shot_type_away['options'] = json.dumps({'title':away_team})

    #unique html chart ids
    chart_ids = df.make_dict(diff_chart = diff_chart['id'], poss_chart_home = poss_chart_home['id'], poss_chart_away = poss_chart_away['id'],
        score_time_chart = score_time_chart['id'], shot_type_chart = shot_type_chart['id'])

    #set misc chart options
    diff_chart['formatters'] = [['0',1]]
    poss_chart_home['formatters'] = [['0.00',1]]
    poss_chart_away['formatters'] = [['0.00',1]]

    #construct a dict to hold all the charts
    column_charts = [diff_chart, poss_chart_home,poss_chart_away]
    line_charts = [score_time_chart]
    pie_diff_charts = [shot_type_chart]

    return render_template(
        'game_scoring.html',
        the_month = the_month,
        the_day = the_day,
        the_year = the_year,
        game_string = game_string,
        column_charts = column_charts,
        line_charts = line_charts,
        pie_diff_charts = pie_diff_charts,
        chart_ids = chart_ids,
        no_game = False)
