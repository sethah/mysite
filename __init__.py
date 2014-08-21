import os
from flask import Flask, Blueprint
from flask.ext.sqlalchemy import SQLAlchemy
from mysite.config_app import basedir
import sys

current_dir =  os.path.dirname(os.path.realpath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

app = Flask(__name__)
app.config.from_object('config_app')
db = SQLAlchemy(app)

from mysite.data_functions import myround
import table_functions as tbl

from mysite.game.views import mod as gameModule
from mysite.teams.views import mod as teamsModule
from mysite.views import mod as mainModule

app.register_blueprint(mainModule)
app.register_blueprint(gameModule)
app.register_blueprint(teamsModule)

class current_season():
    def __init__(self):
        self.current_year = 2014