#Embedded file name: ./mysite/models.py
from mysite import db
from datetime import datetime

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

    def __getitem__(self, key):
        return getattr(self, key)