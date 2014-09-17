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

current_year = df.get_year()

mod = Blueprint('game', __name__, url_prefix='/game')

@mod.route('/<the_month>/<the_day>/<the_year>/<game_string>/box_stats')
def box_stats(the_month, the_day, the_year, game_string):
    #get all the game data and handle errors
    home_team_ss, away_team_ss, date = gf.init_game_data(the_month,the_day,the_year,game_string)

    if date == None:
        #the url is bad
        return redirect(url_for('main.index'))

    #get the db year for the game
    game_year = df.get_year_from_date(date)

    away_team_obj = models.team.query.join(models.year).filter(and_(models.year.year==game_year,models.team.statsheet==away_team_ss)).first()
    home_team_obj = models.team.query.join(models.year).filter(and_(models.year.year==game_year,models.team.statsheet==home_team_ss)).first()
    if away_team_obj == None or home_team_obj == None:
        #one or more teams found
        return render_template('game_scoring.html',no_game = True)


    box_data = models.box_stat.query.join(models.game).filter(and_(models.game.date == date,models.game.away_team == away_team_obj.ncaaID, models.game.home_team == home_team_obj.ncaaID)).all()
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
    names = [bst.name for bst in box_data]

    for bst in box_data:
        #remove the nones from each stat
        for key,val in bst.__dict__.items():
            if getattr(bst,key) == None:
                setattr(bst,key,0)
        if bst.name == home_team_obj.espn_name:
            #this stat is for the home team's totals
            home_team_box = bst
            '''try:
                #todo: fix
                setattr(home_team_box,'name',tf.get_team_param(home_team_box.name,'statsheet').espn_name)
            except: pass'''
        elif bst.name == away_team_obj.espn_name:
            #this stat is for the away team's totals
            away_team_box = bst
            '''try:
                setattr(away_team_box,'name',tf.get_team_param(away_team_box.name,'statsheet').espn_name)
            except: pass'''
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
        current_year = current_year,
        game_string = game_string)

@mod.route('/<the_month>/<the_day>/<the_year>/<game_string>/scoring')
def game_scoring(the_month, the_day, the_year, game_string):

    #get all the game data
    home_team_ss, away_team_ss, date = gf.init_game_data(the_month,the_day,the_year,game_string)

    if date == None:
        #the url is bad
        return redirect(url_for('main.index'))

    #get the db year for the game
    game_year = df.get_year_from_date(date)

    q = tf.query_by_year('team',game_year)
    away_team_obj = q.filter(models.team.statsheet==away_team_ss).first()
    q = tf.query_by_year('team',game_year)
    home_team_obj = q.filter(models.team.statsheet==home_team_ss).first()
    if away_team_obj == None or home_team_obj == None:
        #one or more teams found
        return render_template('game_scoring.html',no_game = True)

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
    game_end_time = int(df.myround(pbp_data[-1].time,game_time_interval,'up'))
    game_time_keys = range(game_end_time+game_time_interval)[0::game_time_interval]

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
        score_triple = [st.time,tooltip,int(st.home_score),int(st.away_score)]
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
                diff_dict[game_time_bin]['val'] += int(st.worth)
            else:
                #away team scored
                diff_dict[game_time_bin]['val'] -= int(st.worth)
        #shot type
        if st.stat_type == 'POINT':
            shot_type = df.shot_type_convert(st.point_type)+'s'
            try:
                shot_type_dict[tms[st.teamID]][shot_type]['val'] += st.worth
            except:
                continue

    #scoring difference chart
    diff_chart = cf.google_chart(chart_type='column',chartid='diff')
    diff_chart.options['hAxis']['title'] = 'Game Time (min)'
    diff_chart.options['vAxis']['title'] = 'Points'
    diff_chart.js_options()

    #home team scoring by possession time chart
    poss_chart_home = cf.google_chart(chart_type='column',chartid='home_poss')
    poss_chart_home.options['hAxis']['title'] = 'Possession Time (sec)'
    poss_chart_home.options['vAxis']['title'] = 'Points'
    poss_chart_home.js_options()

    #away team scoring by possession time chart
    poss_chart_away = cf.google_chart(chart_type='column',chartid='away_poss')
    poss_chart_away.options['hAxis']['title'] = 'Possession Time (sec)'
    poss_chart_away.options['vAxis']['title'] = 'Points'
    poss_chart_away.js_options()

    #score vs time line chart
    score_time_chart = cf.google_chart(chart_type='line',chartid='score_time')
    score_time_chart.data = score_time_data
    score_time_chart.options['hAxis']['title'] = 'Game Time (min)'
    score_time_chart.options['vAxis']['title'] = 'Points'
    score_time_chart.js_options()

    #shot type pie chart
    shot_type_chart = cf.google_chart(chart_type='pie_diff',chartid='shot_type')
    shot_type_chart.js_options()

    #convert dictionary to list of lists for google charts
    diff_chart.data, diff_max_val = df.time_hist_to_google_data(diff_dict,['Possession Time','Scoring Differential'],game_time_interval)
    poss_chart_home.data, poss_home_max_val = df.time_hist_to_google_data(poss_time_dict[home_team],['Possession Time',home_team],poss_time_interval,divide_by='poss')
    poss_chart_away.data, poss_away_max_val = df.time_hist_to_google_data(poss_time_dict[away_team],['Possession Time',away_team],poss_time_interval,divide_by='poss')

    shot_type_chart.data = [['Shot Type','Shots',{ 'role': 'tooltip','p': {'html': 'true'} }]]
    shot_type_chart.data2 = [['Shot Type','Shots',{ 'role': 'tooltip','p': {'html': 'true'} }]]
    tooltip = '<div>test</div>'
    for key in shot_type_dict[home_team].keys():
        shot_type_chart.data.append([str(key),int(shot_type_dict[home_team][key]['val']),tooltip])
    for key in shot_type_dict[away_team].keys():
        shot_type_chart.data2.append([str(key),int(shot_type_dict[away_team][key]['val']),tooltip])

    if poss_home_max_val > poss_away_max_val:
        poss_max_val = poss_home_max_val
    else: poss_max_val = poss_away_max_val

    #unique html chart ids
    chart_ids = df.make_dict(diff_chart = diff_chart.chartid, poss_chart_home = poss_chart_home.chartid,
        poss_chart_away = poss_chart_away.chartid, score_time_chart = score_time_chart.chartid, shot_type_chart = shot_type_chart.chartid)

    #set misc chart options
    diff_chart.formatters = [['0',1]]
    poss_chart_home.formatters = [['0.00',1]]
    poss_chart_away.formatters = [['0.00',1]]

    #construct lists to hold all the charts
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
