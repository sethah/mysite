from flask import render_template, flash, redirect, session, url_for, request, Blueprint
from forms import LoginForm
from mysite import models
import data_functions as df
import team_info_functions as tf
from sqlalchemy import and_, or_
from datetime import datetime

mod = Blueprint('main', __name__)

@mod.route('/')
@mod.route('/index')
def index():
    return render_template('index.html')

@mod.route('/alembic')
def sql_test():
    users = models.User.query.all()
    
    return str(len(users))

@mod.app_errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@mod.app_errorhandler(500)
def internal_error(error):
    #db.session.rollback()
    return render_template('500.html'), 500