'''
Created on Jun 2, 2014

@author: Seth
'''

import time
from mysite import models
from mysite import db
from mysite import team_info_functions as tf
import math
from bs4 import BeautifulSoup

#-------------------------functions----------------------#
def get_play_by_play(home_team, away_team, date, rows, starters):
    '''
    Function: get_play_by_play(player_names,last_names, rows)
    Author: S. Hendrickson 1/11/14
    Return: This function performs a variety of subfunctions in order to process the
    play-by-play data. It turns the textual play descriptions into a parseable
    data table with a multitude of information for each play
    '''

    #make a list to hold all the stat instancess
    st_list = []
    g = 0

    #get the player names



    #PBP data not available if there are <100 rows
    if len(rows) > 100:

        #establish the basic data, putting all stats for the game in 'st'
        pbp_data, N = basic_data_pbp(rows,home_team, away_team,starters)

        #handle timeouts and strange timeout situations
        pbp_data = handle_funky_timeouts(pbp_data,N)

        #process the more complex data
        pbp_data = post_process_pbp(pbp_data,N)

    else:
        #no play by play data available via statsheet OR espn
        pass
    g += 1

    for stat in pbp_data:
        pos_sum = 0

        if stat.possession_time == None:
            stat.possession_time = -1
        stat.possession_time = round(stat.possession_time)
        stat.possession_time_adj = round(stat.possession_time_adj)

    return pbp_data
def string_to_stats(string, names, last_names, first_names, teamID, source):
    '''
    Function: string_to_stats(string, player_list, last_names, teamID, source)
    Author: S. Hendrickson 1/11/14
    Return: This function takes a textual description of a play and returns
    the player, stat type, and a stat tag. The stat tag is used to convey
    more information about some stat types.
    '''

    string = string.replace('(','')
    string = string.replace(')','')
    string = string.upper()
    #all possible distinguishing stat types in the play string
    stat_list = ['MADE',
     'MISSED',
     'REBOUND',
     'ASSIST',
     'BLOCK',
     'STEAL',
     'TURNOVER',
     'FOUL',
     'TIMEOUT']

    if source == 'espn':
        #ESPN shot descriptions
        shot_list = ['THREE POINT',
         'FREE THROW',
         'LAYUP',
         'JUMPER',
         'DUNK',
         'TIP']
    elif source == 'ncaa':
        #ncaa shot descriptions
        shot_list = ['THREE POINT',
         'FREE THROW',
         'LAYUP',
         'TWO POINT',
         'DUNK',
         'TIP']
    else:
        #statsheet shot descriptions
        shot_list = ['3-POINT',
         'FREE THROW',
         'LAYUP',
         '2-POINT',
         'DUNK',
         'TIP']

    #shot types defined, these must be in corresponding order to the shot list
    ptag_list = ['3PM',
     '3PMS',
     'FTM',
     'FTMS',
     'LUM',
     'LUMS',
     'JM',
     'JMS',
     'DM',
     'DMS',
     'TIM',
     'TIMS']

    player = 'NA'
    p = 0
    '''
    There are special cases where first names must be used, but a first name could appear in someone elses
    full name. Example: 'Andre' for 'Andre Hollins' appears in teammate 'Deandre'. So, if first name is
    used, then make sure that the last name is also in the string.
    '''
    for last_name in last_names:
        try:
            first_name = first_names[p]

            #roman numerals screw stuff up
            if ' III' in last_name:
                last_name = last_name.replace(' III','')
            elif ' II' in last_name:
                last_name = last_name.replace(' II','')

            #handle JR. and SR.
            last_name = last_name.replace('.','')


            if last_name.upper() in string:
                #if there is only one player on the team with this last name and the last name is not a first name
                if last_names.count(last_name) == 1 and len([name for name in first_names if last_name in name]) == 0:
                    player = names[p]
                elif first_names[p].upper() in string:
                    player = names[p]
            elif first_name.upper() in string:
                if first_names.count(first_name) == 1 and len([name for name in last_names if first_name in name]) == 0:
                    player = names[p]
                elif last_names[p].upper() in string:
                    player = names[p]
        except:
            #error with names
            p += 1
            continue

        p += 1

    stat_type = ''
    for stat in stat_list:
        #assign the stat type if it is in the string
        if stat in string:
            stat_type = stat
            break

    #assign stat tag if the stat type is a point or rebound
    stat_tag = ''
    if stat_type == 'MADE':
        #change stat type to 'POINT'
        stat_type = 'POINT'

        #assign stat tag the type of shot that it was
        i = 0
        for shot in shot_list:
            if shot in string:
                stat_tag = ptag_list[i * 2]
                break
            i = i + 1

    elif stat_type == 'MISSED':
        #change stat type to 'POINT'
        stat_type = 'POINT'

        #assign stat tag the type of shot that it was
        i = 0
        for shot in shot_list:
            if shot in string:
                stat_tag = ptag_list[i * 2 + 1]
                break
            i = i + 1

    elif stat_type == 'REBOUND':
        #assign stat tag a number to indicate the type of rebound
        if 'OFFENSIVE' in string:
            stat_tag = 0
        elif 'TEAM' in string:
            stat_tag = -1
        else:
            stat_tag = 1
        if 'DEAD' in string:
            #ignore dead ball rebounds
            stat_tag = -2
    return (player, stat_type, stat_tag)


def possession_change(pbp_data, i):
    '''
    Function: possession_change(stats, i)
    Author: S. Hendrickson 1/11/14
    Return: This function detects a possession change from a given play
    '''
    possession_change = False
    #possession change on a make, def reb, turnover, assist, steal, or a charge
    if (pbp_data[i].result == 1) | (pbp_data[i].rebound_type == 1) | (pbp_data[i].stat_type == 'TURNOVER') | (pbp_data[i].stat_type == 'ASSIST') | (pbp_data[i].stat_type == 'STEAL') | (pbp_data[i].charge == 1):
        possession_change = True
    return possession_change
def get_row_data(row):
    '''
    Function: get_row_data(row)
    Author: S. Hendrickson 1/11/14
    Return: This function takes a play by play row and splits it up into
    two play strings (one of which should be empty), two scores, and a
    time.
    '''
    tds = row.findAll('td')


    try:
        #get the time
        tTime = tds[0].get_text().encode('utf-8')
        tTime = tTime[0:5]


        tPlay1 = tds[1].get_text().encode('utf-8')
        playID = 1
        #if there is text in the first column, then playID = 0, 1 otherwise
        if len(tPlay1)>2:
            playID = 0

        #convert score in form '22-23' to a score and opp score
        rawScore = tds[2].get_text().encode('utf-8')
        dash = rawScore.find('-')
        tScore1 = rawScore[0:dash]
        tScore2 = rawScore[dash+1:len(rawScore)]
        tPlay2 = tds[3].get_text().encode('utf-8')
    except:
        tTime = '0'
        tPlay1 = ''
        tPlay2 = ''
        tScore1 = '0'
        tScore2 = '0'
        playID = 0
        print 'bad tr string'

    return playID,tTime,tPlay1,tPlay2,tScore1,tScore2
def basic_data_pbp(rows,home_team, away_team, starters):
    '''
    Function: basic_data_pbp(rows,player_names,source)
    Author: S. Hendrickson 1/11/14
    Return: This function iterates through play by play rows and derives basic
    statistical data. The data is stored in an instance of the stat class and
    returned.
    '''

    i = 0

    pbp_data = []

    #query for all players on the home team, store in hnames
    q = models.player.query.join(models.team).filter(models.team.ncaaID==home_team).all()
    hlast_names = []
    hfirst_names = []
    hnames = []
    for plr in q:
        hlast_names.append(plr.last_name)
        hfirst_names.append(plr.first_name)
        hnames.append(plr.name)

    #query for all players on the away team, store in anames
    q = models.player.query.join(models.team).filter(models.team.ncaaID==away_team).all()
    alast_names = []
    afirst_names = []
    anames = []
    for plr in q:
        alast_names.append(plr.last_name)
        afirst_names.append(plr.first_name)
        anames.append(plr.name)

    #initialize lineups
    home_lineup = ''
    away_lineup = ''
    new_lineup_flag_home = True
    new_lineup_flag_away = True

    #loop through all the rows
    for row in rows:

        st = models.pbp_stat()

        #get the time, each team's score, and the text for each team's column
        try:
            bs_row = BeautifulSoup(row, "html.parser")
        except:
            #bad row string
            bs_row = ''

        playID,tTime,tPlay1,tPlay2,tScore1,tScore2 = get_row_data(bs_row)

        #teamID = 1 for the home team, 0 for away
        teamID = playID

        #write the text string into tPlay
        tPlay = tPlay1
        if playID == 1:
            tPlay = tPlay2

        #extract the type of play and player from the text string
        if playID == 1:
            names = hnames
            last_names = hlast_names
            first_names = hfirst_names
        else:
            names = anames
            last_names = alast_names
            first_names = afirst_names

        player, stat_type, stat_tag = string_to_stats(tPlay, names, last_names, first_names, teamID, 'ncaa')


        #skip dead ball rebounds
        if stat_type == 'REBOUND' and stat_tag < -1:
            continue

        #add and delete players on substitutions
        if 'ENTERS' in tPlay.upper():
            if playID == 1:
                home_lineup = add_to_lineup(home_lineup,player)
            else:
                away_lineup = add_to_lineup(away_lineup,player)
        elif 'LEAVES' in tPlay.upper():
            if playID == 1:
                #if a player is yanked at the start of a half and he wasn't in the lineup then add him to the previous lineups
                if player not in home_lineup and new_lineup_flag_home:
                    pbp_data = correct_lineup(pbp_data,player,i-1,'home')
                    pass
                home_lineup = delete_from_lineup(home_lineup,player)
            else:
                if player not in away_lineup and new_lineup_flag_away:
                    pbp_data = correct_lineup(pbp_data,player,i-1,'away')
                    pass
                away_lineup = delete_from_lineup(away_lineup,player)

        #if the row returned a valid stat type
        if stat_type:
            #assign lineups to current stat
            st.home_lineup = home_lineup
            st.away_lineup = away_lineup

            #reset the new lineup flag as soon as there are 5 players in the lineup for the first time
            if new_lineup_flag_home and len(st.home_lineup.split(',')) >= 6:
                #print tTime, home_lineup, tPlay
                new_lineup_flag_home = False
            if new_lineup_flag_home and len(st.away_lineup.split(',')) >= 6:
                new_lineup_flag_away = False

            try:
                #convert time string to a float
                st.time = 20 - (float(tTime[0:tTime.find(':')]) + float(tTime[tTime.find(':') + 1:len(tTime)]) / 60)
            except:
                #error converting time, skip this stat
                continue


            #handle half transitions
            if (i != 0):
                if (pbp_data[i - 1].time > st.time):
                    st.time = st.time + 20

                    #handles a weird glitch, there cannot be more than [five] minutes between a stat
                    if st.time - pbp_data[i-1].time > 5:
                        continue
                    #handle one overtime
                    if (pbp_data[i - 1].time > 20) & (pbp_data[i - 1].time > st.time):
                        st.time = st.time + 5
                    #handle two overtimes
                    elif (pbp_data[i - 1].time > 40) & (pbp_data[i - 1].time > st.time):
                        st.time = st.time + 5
                    elif (pbp_data[i - 1].time > 45) & (pbp_data[i - 1].time > st.time):
                        st.time = st.time + 5
                    elif (pbp_data[i - 1].time > 50) & (pbp_data[i - 1].time > st.time):
                        st.time = st.time + 5
                    elif (pbp_data[i - 1].time > 55) & (pbp_data[i - 1].time > st.time):
                        st.time = st.time + 5
                    elif (pbp_data[i - 1].time > 60) & (pbp_data[i - 1].time > st.time):
                        st.time = st.time + 5
                    #TODO: handle more overtimes

                #if a half transition, add a 'HALF' stat to the data
                if (st.time > 20) & (pbp_data[i - 1].time <= 20) | (st.time > 40) & (pbp_data[i - 1].time <= 40) | (st.time > 45) & (pbp_data[i - 1].time <= 45):
                    st.stat_type = 'HALF'

                    #store the time at first stat in half in a temp variable
                    tempTime = st.time

                    #give the 'HALF' stat the necessary data
                    st.time = round(st.time, -1)
                    st.home_score = pbp_data[i - 1].home_score
                    st.away_score = pbp_data[i - 1].away_score
                    st.diff_score = pbp_data[i - 1].diff_score
                    st.possession = pbp_data[i - 1].possession

                    #handle possession change for the 'HALF' stat
                    if possession_change(pbp_data, i - 1):
                        pbp_data[i-1].possession_change = 1
                        st.possession = abs(pbp_data[i - 1].possession - 1)
                    #add the half stat
                    pbp_data.append(st)

                    #reset the lineups
                    away_lineup = ''
                    home_lineup = ''
                    new_lineup_flag_home = True
                    new_lineup_flag_away = True

                    #create new stat instance for this play
                    i = i + 1
                    st = models.pbp_stat()
                    st.home_lineup = home_lineup
                    st.away_lineup = away_lineup
                    #create a new stat to hold the current play and initialize it
                    st.time = tempTime

            #assign play info
            st.player = player
            st.stat_type = stat_type
            st.teamID = teamID

            #if the player wasn't in the lineup, add him
            if st.player not in st.home_lineup and st.teamID == 1 and st.player != 'NA':
                st.add_to_lineup(st.player,'home')
                if new_lineup_flag_home and i != 0:
                    pbp_data = correct_lineup(pbp_data, st.player, i-1, 'home')
                #print 'added ' + st.player, tPlay, st.home_lineup
            elif st.player not in st.away_lineup and st.teamID == 0 and st.player != 'NA':
                st.add_to_lineup(st.player,'away')
                if new_lineup_flag_away and i != 0:
                    pbp_data = correct_lineup(pbp_data, st.player, i-1, 'away')

            #assign score to the appropriate team
            st.home_score = tScore2
            st.away_score = tScore1
            st.diff_score = int(float(st.home_score) - float(st.away_score))

            #specific actions for each play type
            if stat_type == 'POINT':
                st.possession = teamID
                st.point_type = stat_tag
                st.result = 1
                #shot missed
                if 'MS' in stat_tag[-2:]:
                    st.result = 0
                st.value = 2
                #three pointer
                if '3' in stat_tag:
                    st.value = 3
                #free throw
                elif 'FT' in stat_tag:
                    st.value = 1
                    k = 1
                    #free throw was and1 if a fg was made at the same time
                    while pbp_data[i - k].time == st.time:
                        if (pbp_data[i - k].player == st.player) & (pbp_data[i - k].result == 1) & (pbp_data[i - k].value > 1):
                            st.and_one = 1
                        k = k + 1
                        if i-k == -1: break
                st.worth = st.result * st.value
            elif stat_type == 'REBOUND':
                #defensive or offensive rebound
                if int(stat_tag) >= 0:
                    st.rebound_type = int(stat_tag)
                #team rebound (counts as defensive rebound)
                elif int(stat_tag) == -1:
                    st.rebound_type = 1
                    #whoever had possession previously still has it for a team rebound
                    if pbp_data[i - 1].possession == teamID:
                        st.rebound_type = 0

                #offensive rebound
                if int(st.rebound_type) == 0:
                    #the current team has possession if it was an offensive rebound
                    st.possession = teamID
                #defensive rebound
                else:
                    #flip the possession
                    st.possession = abs(teamID - 1)

            elif stat_type == 'ASSIST':
                #possession is with the team that made the assist
                st.possession = teamID
                #assign a point value for the assist
                st.value = pbp_data[i - 1].value
                #recipient of the assist was the player who made the previous play
                st.recipient = pbp_data[i - 1].player
                st.point_type = pbp_data[i - 1].point_type
                pbp_data[i - 1].assisted = 1

            elif stat_type == 'FOUL':
                st.possession = abs(teamID - 1)
                if i != 0:
                    #if the foul was a turnover, then it was an offensive foul
                    if (pbp_data[i - 1].stat_type == 'TURNOVER') & (pbp_data[i - 1].time == st.time) & (pbp_data[i - 1].teamID == teamID):
                        st.possession = teamID
                        st.charge = 1

            elif stat_type == 'BLOCK':
                #possession is with the team who did not do the blocking
                st.possession = abs(teamID - 1)

                #make sure that this is not the first possession (should never be)
                if i != 0:
                    if pbp_data[i - 1].value > 1:
                        #previous shot was blocked
                        pbp_data[i - 1].blocked = 1

            elif stat_type == 'TURNOVER':
                #possession is with the team who turned it over
                st.possession = teamID

                if i != 0:
                    #if the previous play was a foul by the same team at the same time as the current play
                    if (pbp_data[i - 1].stat_type == 'FOUL') & (pbp_data[i - 1].time == st.time) & (pbp_data[i - 1].teamID == teamID):
                        #offensive foul, so correct the possession on the previous play
                        pbp_data[i - 1].possession = st.possession
                        pbp_data[i - 1].charge = 1

            elif stat_type == 'STEAL':
                #possession is with the team who did not do the stealing
                st.possession = abs(teamID - 1)

                if i != 0:
                    if pbp_data[i - 1].stat_type == 'TURNOVER':
                        pbp_data[i - 1].stolen = 1

            i = i + 1
            pbp_data.append(st)

            #give new lineups to the lineup variables
            home_lineup = st.home_lineup
            away_lineup = st.away_lineup

    #append a 'HALF' stat to the end
    st = models.pbp_stat()
    st.stat_type = 'HALF'
    st.time = math.ceil(pbp_data[i - 1].time)
    st.home_score = pbp_data[i - 1].home_score
    st.away_score = pbp_data[i - 1].away_score
    st.diff_score = pbp_data[i - 1].diff_score
    st.possession = pbp_data[i - 1].possession
    st.away_lineup = away_lineup
    st.home_lineup = home_lineup
    if possession_change(pbp_data, i - 1):
        pbp_data[i - 1].possession_change = 1
        st.possession = abs(pbp_data[i - 1].possession - 1)
    pbp_data.append(st)

    return pbp_data, i
def handle_funky_timeouts(pbp_data,N):
    '''
    Function: handle_funky_timeouts(st,N)
    Author: S. Hendrickson 1/11/14
    Return: This function handles possessions on timeouts, and handles situations
    when multiple timeouts are called in a row.
    '''

    for j in range(N):
        '''if len(pbp_data[j].home_lineup.split(',')) != 6:
            print pbp_data[j].home_lineup, pbp_data[j].time
        if pbp_data[j].result == None:
            print pbp_data[j].result,pbp_data[j].value'''
        k = 1
        if j != N:
            #k equals the number of consecutive timeouts
            while pbp_data[j+k].stat_type == 'TIMEOUT':
                k = k + 1

        if pbp_data[j].stat_type == 'TIMEOUT':
            #one timeout was called, then half
            if pbp_data[j+1].stat_type== 'HALF':
                #assign possession on the timeout to whoever had possession previously
                pbp_data[j].possession = pbp_data[j-1].possession

                #if the previous play caused a possession change
                if possession_change(pbp_data, j - 1):
                    #correct posession stats
                    pbp_data[j-1].possession_change = 1
                    pbp_data[j].possession = abs(pbp_data[j-1].possession - 1)
                #possession on the half goes to whoever had possession on the timeout
                pbp_data[j + 1].possession = pbp_data[j].possession

            #multiple timeouts called in a row
            else:
                #possession on the timeout goes to whoever had possession out of the timeout
                pbp_data[j].possession = pbp_data[j + k].possession

    return pbp_data
def post_process_pbp(pbp_data,N):
    '''
    Function: post_process_pbp(st,N)
    Author: S. Hendrickson 1/11/14
    Return: This function performs the complex post processing on data that
    already has the basic stats defined.
    '''
    start = time.time()
    #initialize variables
    pos_start = 0
    pos_index = 0
    fTimeout = 0
    fOff_reb = 0
    fTurnover = 0
    run = 0
    fRun = 0
    clutch = 0
    ft_total = 0

    #loop through each play
    for j in range(len(pbp_data)):

        #FUNCTIONALIZE
        if j == 0:
            and_one = 0
            #and_one_worth is used to assign points off <turnover,oreb,timeout>
            and_one_worth = 0

            k = 0
            #iterate while the time is the same
            while pbp_data[j].time == pbp_data[j+k].time:
                #keep track of the worths in case of and1
                if pbp_data[j + k].worth:
                    and_one_worth += pbp_data[j + k].worth
                if pbp_data[j + k].and_one == 1:
                    and_one = 1
                k += 1
            #if no and1, then forget it
            if and_one == 0:
                and_one_worth = 0

        elif (pbp_data[j].time != pbp_data[j-1].time) & (j != N):
            and_one = 0
            and_one_worth = 0
            k = 0
            #same as above
            while pbp_data[j].time == pbp_data[j + k].time and j+k != len(pbp_data)-1:
                if pbp_data[j + k].worth:
                    and_one_worth += pbp_data[j + k].worth
                if pbp_data[j + k].and_one == 1:
                    and_one = 1
                k += 1
            if and_one == 0:
                and_one_worth = 0

        #keep track of the free throw total points for use in "points off" variables
        if pbp_data[j].value == 1:
            #print pbp_data[j].result, pbp_data[j].value
            ft_total += pbp_data[j].worth
        #reset if not a free throw or a timeout
        elif pbp_data[j].stat_type != 'TIMEOUT':
            ft_total = 0

        #FUNCTIONALIZE
        if j != 0:
            #keep track of fouls for both teams
            pbp_data[j].home_fouls = math.floor(float(pbp_data[j-1].home_fouls))
            pbp_data[j].away_fouls = math.floor(float(pbp_data[j-1].away_fouls))
            if pbp_data[j].stat_type == 'FOUL':
                if pbp_data[j].teamID == 1:
                    pbp_data[j].home_fouls = pbp_data[j-1].home_fouls + 1
                if pbp_data[j].teamID == 0:
                    pbp_data[j].away_fouls = pbp_data[j-1].away_fouls + 1
                #add 0.1 to fouls that transition to a bonus for easier processing later
                if (pbp_data[j].home_fouls == 7) & (pbp_data[j].home_fouls < 7) | (pbp_data[j].home_fouls == 10) & (pbp_data[j-1].home_fouls < 10):
                    pbp_data[j].home_fouls += 0.1
                if (pbp_data[j].away_fouls == 7) & (pbp_data[j-1].away_fouls < 7) | (pbp_data[j].away_fouls == 10) & (pbp_data[j-1].away_fouls < 10):
                    pbp_data[j].away_fouls += 0.1
            if (pbp_data[j-1].stat_type == 'HALF') & (pbp_data[j-1].time == 20):
                #reset fouls at halftime
                pbp_data[j].home_fouls = 0
                pbp_data[j].away_fouls = 0
        elif pbp_data[j].stat_type == 'FOUL':
            #handle a foul on the first stat of the game
            if pbp_data[j].teamID == 1:
                pbp_data[j].home_fouls = 1
                pbp_data[j].away_fouls = 0
            if pbp_data[j].teamID == 0:
                pbp_data[j].away_fouls = 1
                pbp_data[j].home_fouls = 0
        else:
            pbp_data[j].home_fouls = 0
            pbp_data[j].away_fouls = 0

        #track clutch time, defined as score diff <= 5 and less than 5 minutes remaining
        if j != 0:
            clutch += clutch_time(pbp_data[j-1].diff_score,pbp_data[j-1].time,pbp_data[j].time,5,5)


        if j != N:
            #possession change if different team has possession than previous stat and some other anomalies are not present
            if (pbp_data[j].possession != pbp_data[j+1].possession) & (pbp_data[j].stat_type != 'HALF') & (not (pbp_data[j+1].stat_type == 'FOUL') & (pbp_data[j+1].time == pbp_data[j].time) & (pbp_data[j].stat_type == 'FOUL') & (pbp_data[j+1].charge == 0)):
                pbp_data[j].possession_change = 1

        #keep track of the index of the last play that the team who had possession made on the possession
        if pbp_data[j].teamID == pbp_data[j].possession:
            pos_index = j

        #special possession handling for halves
        if pbp_data[j].stat_type == 'HALF':
            #assign the length of the last possession to possession time
            pbp_data[j].possession_time= (pbp_data[j].time - pos_start) * 60

            #possession time adjusted assigns the possession time to every play in that possession
            k = 0
            while (pbp_data[j].possession == pbp_data[j-k].possession) & (j - k >= 0):
                pbp_data[j-k].possession_time_adj= pbp_data[j].possession_time
                k += 1

            #reset pos_start and pos_index
            pos_start = pbp_data[j].time
            pos_index = j + 1

            #reset the timeout, oreb, and turnover flags
            fTimeout = 0
            fOff_reb = 0
            fTurnover = 0

        #do possession handling when the possession has changed
        if pbp_data[j].possession_change == 1:
            pbp_data[pos_index].possession_time = (pbp_data[j].time - pos_start) * 60
            pos_start = pbp_data[j].time

            #iterate backwards and assign the possession time to adjusted possession time
            k = 0
            while (pbp_data[j].possession == pbp_data[j - k].possession) & (j - k >= 0):
                pbp_data[j - k].possession_time_adj = pbp_data[pos_index].possession_time
                k += 1

            #not sure about this one
            if j - k == 1:
                if pbp_data[j - k].possession_time == '':
                    pbp_data[j - k].possession_time_adj = pbp_data[j - k + 1].possession_time_adj

        #specific actions for each type of stat
        if pbp_data[j].stat_type == 'POINT':
            if j != 0:
                if pbp_data[j].result == 1:
                    #if a team scores and they were not the last ones to score, reset the run sum
                    if fRun != pbp_data[j].teamID:
                        run = 0
                    fRun = pbp_data[j].teamID

                if pbp_data[j].value > 1:
                    #assign turnover,second chance, and timeout points if this was not an and1
                    '''NOTE: any of these points are reset after the first fg attempt, regardless if there is
                    and offensive rebound that is converted. The oreb points would be assigned, but the points
                    were not scored off a timeout or turnover. This was a choice made by the designer'''
                    if fTurnover == 1:
                        if and_one == 0:
                            pbp_data[j].to_points = pbp_data[j].worth
                            fTurnover = 0
                    if fOff_reb == 1:
                        if and_one == 0:
                            pbp_data[j].second_chance = pbp_data[j].worth
                            fOff_reb = 0
                    if fTimeout == 1:
                        if and_one == 0:
                            pbp_data[j].timeout_points = pbp_data[j].worth
                            fTimeout = 0

                #if play is the last free throw attempt in the sequence
                elif (pbp_data[j + 1].value != 1) & (not (pbp_data[j + 1].stat_type == 'TIMEOUT') & (pbp_data[j + 1].time == pbp_data[j].time)):
                    #assign either the freethrow total or the and one worth
                    if fTurnover == 1:
                        if and_one == 0:
                            pbp_data[j].to_points = ft_total
                        else:
                            pbp_data[j].to_points = and_one_worth
                        fTurnover = 0
                    if fOff_reb == 1:
                        if and_one == 0:
                            pbp_data[j].second_chance = ft_total
                            fOff_reb = 0
                        else:
                            pbp_data[j].second_chance = and_one_worth
                        fOff_reb = 0
                    if fTimeout == 1:
                        if and_one == 0:
                            pbp_data[j].timeout_points = ft_total
                        else:
                            pbp_data[j].timeout_points = and_one_worth
                        fTimeout = 0

            #assign run flag if the first play is a make
            if j == 0 and pbp_data[j].result == 1:
                fRun = pbp_data[j].teamID

            #if the play is a free throw
            if pbp_data[j].value == 1:
                #iterate back through all plays in the possession
                k = 1
                while (pbp_data[j].possession == pbp_data[j - k].possession) & (j - k > 1):
                    #if the player attempting the free throw also made a fg then this is an and1
                    if (pbp_data[j - k].player == pbp_data[j].player) & (pbp_data[j - k].result == 1) & (pbp_data[j - k].value > 1):
                        pbp_data[j].and_one = 1
                    k += 1

            #run is positive for team, and negative for opponent
            run = run - (-1) ** pbp_data[j].teamID * pbp_data[j].worth
        elif pbp_data[j].stat_type == 'REBOUND':
            #if offensive rebound, assign offensive rebound flag
            if int(pbp_data[j].rebound_type) == 0:
                fOff_reb = 1
        elif pbp_data[j].stat_type == 'TIMEOUT':
            #if timeout, assign timeout flag
            fTimeout = 1
        elif pbp_data[j].stat_type == 'TURNOVER':
            #if turnover, assign turnover flag
            if fTurnover == 1:
                pbp_data[j].to_points = 0

            #if a turnover occurs after a oreb, timeout, or opposing team turnover, then points unconverted
            if fOff_reb == 1:
                pbp_data[j].second_chance = 0
                fOff_reb = 0
            if fTimeout == 1:
                pbp_data[j].timeout_points = 0
                fTimeout = 0
            fTurnover = 1

    return pbp_data
def clutch_time(diff_score,time0,time1,clutch_score,clutch_time):
    '''
    Function: clutch_time(diff_score,time0,time1,clutch_score,clutch_time)
    Author: S. Hendrickson 1/11/14
    Return: This function returns clutch time between possessions.
    '''
    time = 0
    if abs(diff_score) <= clutch_score:
        if (time0 < 40-clutch_time) & (time1 >= 40-clutch_time):
            time = time1 - (40-clutch_time)
        elif time0 >= (40-clutch_time):
            time = time1-time0
    if time < 0:
        time = 0
    return time
def add_to_lineup(lineup,name):
    new_lineup = lineup.split(',')
    if name not in new_lineup:
        new_lineup.append(name)
        new_lineup = ','.join(new_lineup)
        return new_lineup
    else:
        return lineup
def delete_from_lineup(lineup,name):
    new_lineup = lineup.split(',')
    if name in new_lineup:
        new_lineup.remove(name)
        new_lineup = ','.join(new_lineup)
        return new_lineup
    else:
        return lineup
def correct_lineup(stats, name, index, team):
    try:
        if team == 'home':
            while len(stats[index].home_lineup.split(',')) < 6:
                stats[index].home_lineup = add_to_lineup(stats[index].home_lineup,name)
                index -= 1
                if index < 0:
                    break
            return stats
        else:
            while len(stats[index].away_lineup.split(',')) < 6:
                stats[index].away_lineup = add_to_lineup(stats[index].away_lineup,name)
                index -= 1
                if index < 0:
                    break
            return stats
    except IndexError:
        print index, len(stats)
        return stats

#----------------------------------------------------------------------
#Box stat functions
#----------------------------------------------------------------------
def get_box_stat_game(home_team, away_team, home_outcome, date, rows):

    #these headers are the headers used by stats.ncaa's box scores
    hdrs = ['Player', 'Pos','MP','FGM','FGA','3FG','3FGA','FT','FTA','PTS','ORebs','DRebs','Tot Reb','AST','TO','STL','BLK','Fouls']

    #empty list to hold the box stat class instances
    box_data = []
    #max_score variable will be used to determine who won the game
    max_score = 0
    for row in rows:
        bstat = models.box_stat()

        #convert row to bs object for easier parsing
        try:
            row = BeautifulSoup(row,"html.parser")
            tds = row.findAll('td')
        except:
            tds = []

        #column index for each row
        k = 0
        for td in tds:
            string = td.get_text().strip()
            if string == '':
                #ignore empty cells
                k += 1
                continue
            try:
                if hdrs[k] == 'Player':
                    if string != 'TEAM' and string != 'Totals':
                        #if it's not a totals row
                        bstat.name, bstat.first_name, bstat.last_name = tf.convert_name_ncaa(string)
                    elif string == 'Totals':
                        bstat.name = 'Totals'
                elif hdrs[k] == 'Pos':
                    #position cell is blank for non starters
                    if string != '':
                        bstat.started = True
                elif hdrs[k] == 'MP':
                    if ':' in string:
                        val = int(string[0:string.find(':')])
                        bstat = make_box_stat(hdrs[k],bstat,val)
                else:
                    #some of the values have a '/' appended, so remove it
                    val = int(string.replace('/',''))
                    bstat = make_box_stat(hdrs[k],bstat,val)
                    #TODO: use setattr

                    if hdrs[k] == 'PTS':
                        max_score = max(max_score,val)
            except:
                #error with assiging cell value to stat
                k += 1
                continue
            k += 1
        #append each row as a box stat
        box_data.append(bstat)

    #format team totals stats
    for st in box_data:
        try:
            if st.name == 'Totals':
                if st.pts == max_score:
                    #this team won the game
                    if home_outcome == 'W':
                        st.name = tf.get_team_param(home_team,'ncaa','statsheet')
                    else:
                        st.name = tf.get_team_param(away_team,'ncaa','statsheet')
                else:
                    #this team lost the game
                    if home_outcome == 'L':
                        st.name = tf.get_team_param(home_team,'ncaa','statsheet')
                    else:
                        st.name = tf.get_team_param(away_team,'ncaa','statsheet')
            else:
                continue
        except:
            continue
    return box_data

def make_box_stat(hdr,bstat,val):
    '''
    @summary: Consolidates
    '''
    if hdr == 'PTS':
        bstat.pts = val
    elif hdr == 'MP' or hdr == 'MIN':
        bstat.min = val
    elif hdr == 'FGM':
        bstat.fgm = val
    elif hdr == 'FGA':
        bstat.fga = val
    elif hdr == '3FGA' or hdr == '3PA':
        bstat.tpa = val
    elif hdr == '3FG' or hdr == '3PM':
        bstat.tpm = val
    elif hdr == 'FT':
        bstat.ftm = val
    elif hdr == 'FTA':
        bstat.fta = val
    elif hdr == 'OREB' or hdr == 'OR' or hdr == 'OFFR' or hdr == 'ORebs':
        bstat.oreb = val
    elif hdr == 'DREB' or hdr == 'DR' or hdr == 'DEFR' or hdr == 'DRebs':
        bstat.dreb = val
    elif hdr == 'REB' or hdr == 'Tot Reb':
        bstat.reb = val
    elif hdr == 'AST':
        bstat.ast = val
    elif hdr == 'STL':
        bstat.stl = val
    elif hdr == 'BLK':
        bstat.blk = val
    elif hdr == 'TO':
        bstat.to = val
    elif hdr == 'PF' or hdr == 'Fouls':
        bstat.pf = val
    return bstat
def check_game_stats(pbp_game):

    home_team = pbp_game.home_team
    away_team = pbp_game.away_team

    q = models.player.query.join(models.team).filter(models.team.ncaaID==home_team).all()
    home_roster = []
    for plr in q:
        home_roster.append(plr.name)

    q = models.player.query.join(models.team).filter(models.team.ncaaID==away_team).all()
    away_roster = []
    for plr in q:
        away_roster.append(plr.name)

    chk_stats = ['pts','fga','fgm','tpa','tpm','fta','ftm','reb','dreb','oreb','to','pf','ast','blk','stl']

    res = {}
    for name in away_roster:
        res[name] = {}
        for hdr in chk_stats:
            res[name][hdr] = 0
    for name in home_roster:
        res[name] = {}
        for hdr in chk_stats:
            res[name][hdr] = 0

    for st in pbp_game.pbp_data:
        if st.player == 'NA':
            continue

        if st.stat_type == 'POINT':
            res[st.player]['pts'] += st.worth

            if st.value > 1:
                #field goal
                res[st.player]['fga'] += 1
                res[st.player]['fgm'] += st.result

                if st.value == 3:
                    #3 pointer
                    res[st.player]['tpa'] += 1
                    res[st.player]['tpm'] += st.result
            else:
                #free throw
                res[st.player]['fta'] += 1
                res[st.player]['ftm'] += st.result
        elif st.stat_type == 'ASSIST':
            res[st.player]['ast'] += 1
        elif st.stat_type == 'TURNOVER':
            res[st.player]['to'] += 1
        elif st.stat_type == 'REBOUND':
            res[st.player]['reb'] += 1
            if int(st.rebound_type) == 1:
                res[st.player]['dreb'] += 1
            elif int(st.rebound_type) == 0:
                res[st.player]['oreb'] += 1
        elif st.stat_type == 'BLOCK':
            res[st.player]['blk'] += 1
        elif st.stat_type == 'STEAL':
            res[st.player]['stl'] += 1
        elif st.stat_type == 'FOUL':
            res[st.player]['pf'] += 1

    plrs = res.keys()
    names = []
    for bst in pbp_game.box_data:
        for hdr in chk_stats:
            #subtract from the box stat total, and you should end up at zero eventually
            if str(bst.name) in home_roster or str(bst.name) in away_roster:
                val = getattr(bst,hdr)
                if val == None:
                    val = 0
                res[str(bst.name)][hdr] -= val
                if bst.name not in names:
                    names.append(bst.name)

    for name in names:
        for key in res[name].keys():
            if abs(res[name][key]) > 0:
                print name, key, res[name][key], tf.get_team_param(home_team,'ncaa','statsheet'), tf.get_team_param(away_team,'ncaa','statsheet')

def check_poss_time(pbp_game):

    home_team = pbp_game.home_team
    away_team = pbp_game.away_team
    date = pbp_game.date
    home_outcome = pbp_game.home_outcome

    try:
        home_team = tf.get_team_param(home_team, 'statsheet')
    except:
        home_team = ''
    try:
        away_team = tf.get_team_param(away_team, 'statsheet')
    except:
        away_team = ''
    poss_time = 0
    for st in pbp_game.pbp_data:
        if st.possession_time > -1:
            poss_time += st.possession_time
        if st.possession_time > 70:
            pass
    if poss_time != 2400 and poss_time != 2700 and poss_time != 3000 or True:
        pass
        print home_team, away_team, poss_time, date
def get_home_outcome(pbp_data):
    try:
        if int(pbp_data[-1].home_score) > int(pbp_data[-1].away_score):
            home_outcome = 'W'
        else:
            home_outcome = 'L'
    except:
        print 'bad outcome'
        home_outcome = None
    return home_outcome