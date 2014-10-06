#Embedded file name: ./mysite/models.py
from mysite import db
from datetime import datetime
import urllib2
import cookielib
import httplib
from bs4 import BeautifulSoup
from sqlalchemy import and_, or_

class team(db.Model):
    __tablename__ = 'team'
    __bind_key__ = 'data_db'
    id = db.Column(db.Integer, primary_key=True)
    #yearid = db.Column(db.Integer, db.ForeignKey(year.id))
    ncaaID = db.Column(db.String(140))
    statsheet = db.Column(db.String(140))
    ncaa = db.Column(db.String(140))
    espn_name = db.Column(db.String(140))
    espn = db.Column(db.String(140))
    cbs1 = db.Column(db.String(140))
    cbs2 = db.Column(db.String(140))
    rpi_rank = db.Column(db.String(140))
    wins = db.Column(db.String(140))
    losses = db.Column(db.String(140))
    rpi = db.Column(db.String(140))
    sos = db.Column(db.String(140))
    sos_rank = db.Column(db.String(140))
    conference = db.Column(db.String(140))
    players = db.relationship('player', backref='team', lazy='dynamic')

    def __getitem__(self, key):
        return getattr(self, key)
    def __repr__(self):
        return '<%s %s>' % (
            self.ncaaID, self.statsheet)

class raw_game(db.Model):
    __tablename__ = 'raw_game'
    __bind_key__ = 'data_db'
    id = db.Column(db.Integer, primary_key=True)
    home_team = db.Column(db.String(140))
    away_team = db.Column(db.String(140))
    date = db.Column(db.String(140))
    home_outcome = db.Column(db.String(140))
    raw_box_stats = db.relationship('raw_box',cascade='all,delete', backref='raw_game', lazy='dynamic',primaryjoin="raw_box.raw_game_id==raw_game.id")
    raw_pbp_stats = db.relationship('raw_play', cascade='all,delete', backref='raw_game', lazy='dynamic',primaryjoin="raw_play.raw_game_id==raw_game.id")

    def date_string(self):
        date_format = '%m/%d/%Y'
        try:
            return datetime.strftime(self.date,date_format)
        except:
            return None

    @staticmethod
    def get_or_create(date, home_team, away_team):
        g = raw_game.query.filter(or_(and_(raw_game.date==date,raw_game.home_team==home_team,raw_game.away_team==away_team),
                                        and_(raw_game.date==date,raw_game.away_team==home_team,raw_game.home_team==away_team))).first()
        if g is None:
            #the game doesn't exist
            g = raw_game()
            g.date = date
            db.session.add(g)
            print 'new raw game created'
        return g

    def __getitem__(self, key):
        return getattr(self, key)

class raw_play(db.Model):
    __tablename__ = 'raw_play'
    __bind_key__ = 'data_db'
    id = db.Column(db.Integer, primary_key=True)
    raw_game_id = db.Column(db.Integer, db.ForeignKey(raw_game.id))
    soup_string = db.Column(db.String(1000))
class raw_box(db.Model):
    __tablename__ = 'raw_box'
    __bind_key__ = 'data_db'
    id = db.Column(db.Integer, primary_key=True)
    raw_game_id = db.Column(db.Integer, db.ForeignKey(raw_game.id))
    soup_string = db.Column(db.String(1000))



class player(db.Model):
    __tablename__ = 'players'
    __bind_key__ = 'data_db'
    id = db.Column(db.Integer, primary_key=True)
    teamid = db.Column(db.Integer, db.ForeignKey(team.id))
    year = db.Column(db.Integer)
    name = db.Column(db.String(140))
    first_name = db.Column(db.String(140))
    last_name = db.Column(db.String(140))
    pclass = db.Column(db.String(140))
    height = db.Column(db.String(140))
    position = db.Column(db.String(140))

    def height_string(self):
        try:
            ft = int(self.height)/12
            inches = int(self.height) % 12
            return str(ft)+"'"+str(inches)+'"'
        except:
            return self.height
    def __getitem__(self, key):
        return getattr(self, key)

    def __repr__(self):
        return '<%s %s %s %s>' % (
            self.name, self.height, self.pclass,
            self.position)


class game(db.Model):
    __tablename__ = 'game'
    __bind_key__ = 'data_db'
    id = db.Column(db.Integer, primary_key=True)
    home_team = db.Column(db.String(100))
    away_team = db.Column(db.String(100))
    home_outcome = db.Column(db.String(1))
    home_score = db.Column(db.Integer)
    away_score = db.Column(db.Integer)
    neutral_site = db.Column(db.Boolean)
    date = db.Column(db.DateTime)
    pbp_stats = db.relationship('pbp_stat', backref='game', lazy='dynamic',primaryjoin="pbp_stat.gameid==game.id")
    box_stats = db.relationship('box_stat', backref='game', lazy='dynamic',primaryjoin="box_stat.gameid==game.id")

    def date_string(self):
        date_format = '%m/%d/%Y'
        try:
            return datetime.strftime(self.date,date_format)
        except:
            return None

    @staticmethod
    def get_or_create(the_date, home_team, away_team, home_outcome):
        new = False
        g = game.query.filter(or_(and_(game.date==the_date,game.home_team==home_team,game.away_team==away_team),
                                        and_(game.date==the_date,game.away_team==home_team,game.home_team==away_team))).first()
        if g is None:
            #the game doesn't exist
            new = True
            g = game()
            g.home_team = home_team
            g.away_team = away_team
            g.home_outcome = home_outcome
            g.date = the_date
            db.session.add(g)
            print 'new game created'
        else:
            g.home_team = home_team
            g.away_team = away_team
        return g, new

    def __getitem__(self, key):
        return getattr(self, key)
    def __repr__(self):
        return '<%s %s %s %s>' % (
            self.home_team, self.away_team, self.home_score, self.away_score)


class box_stat(db.Model):
    __tablename__ = 'box_stat'
    __bind_key__ = 'data_db'
    id = db.Column(db.Integer, primary_key=True)
    gameid = db.Column(db.Integer, db.ForeignKey(game.id))
    name = db.Column(db.String(140))
    first_name = db.Column(db.String(140))
    last_name = db.Column(db.String(140))
    started = db.Column(db.Integer)
    min = db.Column(db.Integer)
    pts = db.Column(db.Integer)
    fgm = db.Column(db.Integer)
    fga = db.Column(db.Integer)
    tpm = db.Column(db.Integer)
    tpa = db.Column(db.Integer)
    ftm = db.Column(db.Integer)
    fta = db.Column(db.Integer)
    oreb = db.Column(db.Integer)
    dreb = db.Column(db.Integer)
    reb = db.Column(db.Integer)
    ast = db.Column(db.Integer)
    stl = db.Column(db.Integer)
    blk = db.Column(db.Integer)
    to = db.Column(db.Integer)
    pf = db.Column(db.Integer)

    def __getitem__(self, key):
        return getattr(self, key)


class pbp_stat(db.Model):
    __tablename__ = 'pbp'
    __bind_key__ = 'data_db'
    id = db.Column(db.Integer, primary_key=True)
    gameid = db.Column(db.Integer, db.ForeignKey(game.id))
    time = db.Column(db.Float)
    player = db.Column(db.String(140), default = "NA")
    stat_type = db.Column(db.String(70))
    teamID = db.Column(db.Integer)
    home_score = db.Column(db.Integer)
    away_score = db.Column(db.Integer)
    diff_score = db.Column(db.Integer)
    possession = db.Column(db.Integer)
    point_type = db.Column(db.String(20))
    result = db.Column(db.Integer)
    value = db.Column(db.Integer)
    worth = db.Column(db.Integer)
    and_one = db.Column(db.String(2))
    rebound_type = db.Column(db.Integer)
    recipient = db.Column(db.String(140))
    assisted = db.Column(db.Integer)
    charge = db.Column(db.Integer)
    stolen = db.Column(db.Integer)
    blocked = db.Column(db.Integer)
    possession_change = db.Column(db.Integer)
    home_fouls = db.Column(db.Float)
    away_fouls = db.Column(db.Float)
    second_chance = db.Column(db.Integer)
    to_points = db.Column(db.Integer)
    timeout_points = db.Column(db.Integer)
    possession_time = db.Column(db.Integer, default=-1)
    possession_time_adj = db.Column(db.Integer)
    home_lineup = db.Column(db.String(300), default='')
    away_lineup = db.Column(db.String(300), default='')

    def __getitem__(self, key):
        return getattr(self, key)

    def add_to_lineup(self,name,team):
        if team == 'home':
            lineup = self.home_lineup.split(',')
            if name not in lineup:
                lineup.append(name)
                self.home_lineup = ','.join(lineup)
        elif team == 'away':
            lineup = self.away_lineup.split(',')
            if name not in lineup:
                lineup.append(name)
                self.away_lineup = ','.join(lineup)
    def delete_from_lineup(self,name,team):
        if team == 'home':
            lineup = self.home_lineup.split(',')
            if name in lineup:
                lineup.remove(name)
                self.home_lineup = ','.join(lineup)
        elif team == 'away':
            lineup = self.away_lineup.split(',')
            if name in lineup:
                lineup.remove(name)
                self.away_lineup = ','.join(lineup)
    def __repr__(self):
        return '<%s %s %s>' % (
            self.teamID, self.player, self.stat_type)

class Page_Opener:

    def __init__(self):
        self.cookiejar = cookielib.LWPCookieJar()
        self.opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.cookiejar))
        self.agent = 'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; NeosBrowser; .NET CLR 1.1.4322; .NET CLR 2.0.50727)'
        self.headers = {'User-Agent': self.agent}

    def open_and_soup(self, url, data=None):
        print url
        req = urllib2.Request(url, data=None, headers=self.headers)
        try:
            response = self.opener.open(req)
        except httplib.BadStatusLine as e:
            print e, e.line
        else:
            print 'Success'

        the_page = response.read()
        soup = BeautifulSoup(the_page)
        return soup
'''class raw_teams_year(db.Model):
    __tablename__ = 'raw_teams_year'
    __bind_key__ = 'all_teams_db'
    id = db.Column(db.Integer, primary_key=True)
    year = db.Column(db.Integer)
    raw_teams = db.relationship('raw_team', backref='raw_teams_year', lazy='dynamic')


    def __getitem__(self, key):
        return getattr(self, key)'''
class raw_team(db.Model):
    __tablename__ = 'raw_teams'
    __bind_key__ = 'all_teams_db'
    id = db.Column(db.Integer, primary_key=True)
    #yearid = db.Column(db.Integer, db.ForeignKey(raw_teams_year.id))
    ncaaID = db.Column(db.String(140))
    statsheet = db.Column(db.String(140))
    ncaa = db.Column(db.String(140))
    espn_name = db.Column(db.String(140))
    espn = db.Column(db.String(140))
    cbs1 = db.Column(db.String(140))
    cbs2 = db.Column(db.String(140))

    def __getitem__(self, key):
        return getattr(self, key)