'''
Created on May 20, 2014

@author: Seth
'''
from mysite import models

def get_soup(link):
    po = models.Page_Opener()
    try:
        soup = po.open_and_soup(link)
    except:
        #error connecting to link
        soup = None

    return soup


