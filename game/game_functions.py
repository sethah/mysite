import team_info_functions as tf
from datetime import datetime

def init_game_data(month,day,year,game_string):
    #the game string should be two teams separated by '@'
    if game_string.count('@') == 1:
        teams = game_string.split('@')
        home_team_ss = teams[1]
        away_team_ss=  teams[0]
    else:
        home_team_ss = None
        away_team_ss=  None

    #handle date being in wrong format
    try:
        date = datetime.strptime('-'.join([year,month,day]),'%Y-%m-%d')
    except ValueError:
        date = None

    if home_team_ss == None or away_team_ss == None or date == None:
        return None, None, None
    else:
        return home_team_ss, away_team_ss, date