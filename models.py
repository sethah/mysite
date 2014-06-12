#Embedded file name: ./mysite/models.py
from mysite import db
from datetime import datetime
import urllib2
import cookielib
import httplib
from bs4 import BeautifulSoup
ROLE_USER = 0
ROLE_ADMIN = 1

class Page_Opener:

    def __init__(self):
        self.cookiejar = cookielib.LWPCookieJar()
        self.opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.cookiejar))
        self.agent = 'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; NeosBrowser; .NET CLR 1.1.4322; .NET CLR 2.0.50727)'
        self.headers = {'User-Agent': self.agent}

    def open_and_soup(self, url, data=None):
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


class team(db.Model):
    __tablename__ = 'team'
    id = db.Column(db.Integer, primary_key=True)
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

class raw_game:
    def __init__(self):
        self.rows = []
        self.box_rows = []
        self.home_team = ''
        self.away_team = ''
        self.date = ''
        self.location = ''
        self.home_outcome = ''
        
class player(db.Model):
    __tablename__ = 'players'
    id = db.Column(db.Integer, primary_key=True)
    teamid = db.Column(db.Integer, db.ForeignKey(team.id))
    name = db.Column(db.String(140))
    first_name = db.Column(db.String(140))
    last_name = db.Column(db.String(140))
    pclass = db.Column(db.String(140))
    height = db.Column(db.String(140))
    position = db.Column(db.String(140))

    def __getitem__(self, key):
        return getattr(self, key)


class game(db.Model):
    __tablename__ = 'game'
    id = db.Column(db.Integer, primary_key=True)
    home_team = db.Column(db.String(100))
    away_team = db.Column(db.String(100))
    home_outcome = db.Column(db.String(1))
    home_score = db.Column(db.Integer)
    away_score = db.Column(db.Integer)
    neutral_site = db.Column(db.Boolean)
    date = db.Column(db.DateTime)
    pbp_stats = db.relationship('pbp_stat', backref='game')

    def __getitem__(self, key):
        return getattr(self, key)


class box_stat(db.Model):
    __tablename__ = 'box'
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
    #TODO: decrease size by using calculated values
    __tablename__ = 'pbp'
    id = db.Column(db.Integer, primary_key=True)
    gameid = db.Column(db.Integer, db.ForeignKey(game.id))
    time = db.Column(db.Float)
    player = db.Column(db.String(140))
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
    recipient = db.Column(db.Integer)
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
    possession_time = db.Column(db.Integer)
    possession_time_adj = db.Column(db.Integer)
    home_lineup = db.Column(db.String(300))
    away_lineup = db.Column(db.String(300))

    def __getitem__(self, key):
        return getattr(self, key)


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    nickname = db.Column(db.String(64), index=True, unique=True)
    name = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    role = db.Column(db.SmallInteger, default=ROLE_USER)

    def __getitem__(self, key):
        return getattr(self, key)

    def __repr__(self):
        return '<User %r>' % self.nickname