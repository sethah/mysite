
import models
import os
from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.login import LoginManager
from flask.ext.openid import OpenID
from mysite.config_app import basedir

app = Flask(__name__)
app.config.from_object('config')
db = SQLAlchemy(app)

db.create_all()