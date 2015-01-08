import os

CSRF_ENABLED = True
SECRET_KEY = 'you-will-never-guess'
current_year = 2014

OPENID_PROVIDERS = [
    { 'name': 'Google', 'url': 'https://www.google.com/accounts/o8/id' },
    { 'name': 'Yahoo', 'url': 'https://me.yahoo.com' },
    { 'name': 'AOL', 'url': 'http://openid.aol.com/<username>' },
    { 'name': 'Flickr', 'url': 'http://www.flickr.com/<username>' },
    { 'name': 'MyOpenID', 'url': 'https://www.myopenid.com' }]

basedir = os.path.abspath(os.path.dirname(__file__))

SQLALCHEMY_DATABASE_URI_DATA = 'mysql://hendris:Hoo16sier@mysql.server/hendris$data?charset=utf8'
SQLALCHEMY_DATABASE_URI_DATA = 'mysql://hendris:Hoo16sier@127.0.0.1/hendris$data?charset=utf8'
SQLALCHEMY_DATABASE_URI_RAW = 'mysql://hendris:Hoo16sier@mysql.server/hendris$raw_data?charset=utf8'
#SQLALCHEMY_DATABASE_URI_DATA = 'sqlite:///' + os.path.join(basedir, 'foo5.db')
SQLALCHEMY_DATABASE_URI_TEAMS = 'sqlite:///' + os.path.join(basedir, 'raw_teams_'+str(current_year)+'.db')
SQLALCHEMY_POOL_RECYCLE = 499
SQLALCHEMY_BINDS = {
    'data_db' : SQLALCHEMY_DATABASE_URI_DATA,
    'raw_data_db' : SQLALCHEMY_DATABASE_URI_DATA,
    'all_teams_db' : SQLALCHEMY_DATABASE_URI_TEAMS}
#SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'foo5.db')
SQLALCHEMY_MIGRATE_REPO = os.path.join(basedir, 'db_repository')