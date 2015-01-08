
from datetime import datetime
from flask import flash
#from mysite import models
from sqlalchemy import and_, or_
def main():
    yr = get_year_from_date(datetime(2014,2,21))
def get_year():
    current_year = 2014
    return current_year
def ncaa_yr_index(year):
    yrs = [2014,2013,2012,2011,2010,2009]
    idxs = [12020, 11540, 11220, 10740, 10440, 10260]
    try:
        idx = yrs.index(year)
        index = idxs[idx]
    except:
        return None
    return index
def is_int(string):
    try:
        int(string)
        return True
    except:
        return False
def xstr(s):
    if s is None:
        return ''
    return str(s)
def date_range(year):
    date_start = datetime(year,9,1).date()
    date_end = datetime(year+1,5,1).date()
    return [date_start,date_end]
def get_year_from_date(date):
    transition_month = 9
    try:
        year = date.year
        month = date.month
        if month >= transition_month:
            new_year = year
        else:
            new_year = year - 1
    except:
        return None
    return new_year
def myround(num, divisor, round_type = 'down',game_time = False):

    if game_time:
        if int(num) in range(100)[40::5]  :
            num = num-0.0001

    if round_type == 'down':
        rounded = num - (num%divisor)
    else:
        if (num%divisor) == 0:
            rounded = num
        else:
            rounded = num + divisor - (num%divisor)
    return rounded

def time_hist_to_google_data(the_dict,hdr,interval,divide_by = ''):
    #define defaults
    default_color = 'blue'
    max_val = 0

    #try:
    google_data = [hdr]
    the_keys = sorted(the_dict.keys())
    try:
        for key in the_keys:
            if the_dict[key]['color'] == '':
                color = default_color
            else:
                color = the_dict[key]['color']
            if divide_by == '':
                val = the_dict[key]['val']
            else:
                div = the_dict[key][divide_by]
                if div < 0.00001:
                    val = 0
                else:
                    val = the_dict[key]['val']/float(div)
            if val > max_val:
                max_val = val
            google_data.append([str(key)+'-'+str(key+interval),val])
    except:
        #return empty list on bad data
        google_data = []
    return google_data, max_val
def make_dict(**kwargs):
    return kwargs
def shot_type_convert(shot_type):
    shot_string = ''
    if shot_type == 'DM' or shot_type == 'DMS':
        shot_string = 'Dunk'
    elif shot_type == 'FTM' or shot_type == 'FTMS':
        shot_string = 'Free Throw'
    elif shot_type == 'LUM' or shot_type == 'LUMS':
        shot_string = 'Layup'
    elif shot_type == '3PM' or shot_type == '3PMS':
        shot_string = 'Three Pointer'
    elif shot_type == 'JM' or shot_type == 'JMS':
        shot_string = 'Jumper'
    elif shot_type == 'TIM' or shot_type == 'TIMS':
        shot_string = 'Tip-In'
    return shot_string
def shot_list(key = 'string'):
    shot_dict = {}
    shot_dict['string'] = ['Dunk','Layup','Tip-In','Jumper','Three Pointer','Free Throw']

    return shot_dict[key]
def current_team(teamID, team, home_team, away_team):
    current_team = None
    if teamID == 1:
        if home_team == team:
            current_team = 'team'
        else:
            current_team = 'opp'
    elif teamID == 0:
        if home_team == team:
            current_team = 'opp'
        else:
            current_team = 'team'
    return current_team
'''def custom_filter(query, filter_field, filter_field_value, filter_value):
    if filter_field == 'location':
        if filter_field_value == 'Home':
            q = query.filter(models.game.home_team == filter_value)
        elif filter_field_value == 'Away':
            q = query.filter(models.game.away_team == filter_value)
        else:
            q = query
    elif filter_field == 'outcome':
        if filter_field_value == 'Wins':
            q = query.filter(or_(and_(models.game.home_team == filter_value, models.game.home_outcome == 'W'),and_(models.game.away_team == filter_value, models.game.home_outcome == 'L')))
        elif filter_field_value == 'Losses':
            q = query.filter(or_(and_(models.game.home_team == filter_value, models.game.home_outcome == 'L'),and_(models.game.away_team == filter_value, models.game.home_outcome == 'W')))
        else:
            q = query

    return q'''
'''def process_filter(form, q, **kwargs):
    keys = form.keys()
    for key in keys:
        if key == 'location':
            if filter_value == 'Home':
                q = q.filter(models.game.home_team == filter_value)
            elif filter_field_value == 'Away':
                q = q.filter(models.game.away_team == filter_value)
            else:
                q = q
        elif key == 'outcome':
            if filter_field_value == 'Wins':
                q = q.filter(or_(and_(models.game.home_team == filter_value, models.game.home_outcome == 'W'),and_(models.game.away_team == filter_value, models.game.home_outcome == 'L')))
            elif filter_field_value == 'Losses':
                q = q.filter(or_(and_(models.game.home_team == filter_value, models.game.home_outcome == 'L'),and_(models.game.away_team == filter_value, models.game.home_outcome == 'W')))
            else:
                q = q

    for field in filter_fields:
        if field not in keys:
            continue
        if field == 'location':
            q = custom_filter(q, field, form['location'], kwargs['team_obj'].ncaaID)
        elif field == 'outcome':
            q = custom_filter(q, field, form['outcome'], kwargs['team_obj'].ncaaID)

    return q'''
if __name__ == '__main__':
    main()