from datetime import datetime


def init_game_data(month,day,year,game_string):
    #the game string should be two teams separated by '@'
    if game_string.count('@') == 1:
        teams = game_string.split('@')
        home_team_slug = teams[1]
        away_team_slug=  teams[0]
        away_team_obj = models.team.filter(models.team.statsheet==away_team_ss).first()
        home_team_obj = models.team.filter(models.team.statsheet==home_team_ss).first()
    else:
        home_team_obj = None
        away_team_obj =  None

    #handle date being in wrong format
    try:
        date = datetime.strptime('-'.join([year,month,day]),'%Y-%m-%d')
    except ValueError:
        date = None

    if home_team_obj == None or away_team_obj == None or date == None:
        return None, None, None
    else:
        return home_team_obj, away_team_obj, date