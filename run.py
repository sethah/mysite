'''
Created on May 19, 2014

@author: Seth
'''
import os, sys
dir = 'C:\\Users\\Seth\\workspace\\stats_website\\src\\mysite'
if dir not in sys.path:
    sys.path.insert(0,dir)
print sys.path
from mysite import app
app.run(debug = True)
