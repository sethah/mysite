import os, sys
#change working directory to this path
try:
    #for PA execution
    os.chdir('/home/hendris/mysite')
except:
    #for local execution
    os.chdir('C:\\Users\\Seth\\workspace\\stats_website\\src')

project_home = u'/home/hendris'
if project_home not in sys.path:
    sys.path = [project_home] + sys.path

import numpy as np
import scipy.stats.stats as st
from mysite import models
from datetime import datetime
from mysite import link_functions as lf
from mysite import data_functions as df
from mysite import db
np.seterr(divide='ignore', invalid='ignore')

def main():
    q = models.team.query.order_by(models.team.ncaaID).all()
    alpha_dict = {}
    index_vector = []
    for tm in q:
        alpha_dict[tm.ncaaID] = []
        index_vector.append(tm.ncaaID)

    d1 = datetime.strptime('11/10/2014','%m/%d/%Y').date()
    d2 = datetime.strptime('11/21/2014','%m/%d/%Y').date()

    q = models.game.query.filter(models.game.date.between(d1,d2)).limit(3000).all()
    for game in q:
        if not(df.is_int(game.home_team)) or not(df.is_int(game.away_team)):
            continue
        hst, ast = get_team_box_stats(game)
        if hst is None or ast is None:
            print 'None stats', game
            continue
        home_vec = [hst.min,hst.fgm,hst.fga,hst.tpm,hst.tpa,hst.ftm,hst.fta,hst.pts,hst.oreb,hst.dreb,hst.reb,hst.ast,hst.to,hst.pf]
        away_vec = [ast.min,ast.fgm,ast.fga,ast.tpm,ast.tpa,ast.ftm,ast.fta,ast.pts,ast.oreb,ast.dreb,ast.reb,ast.ast,ast.to,ast.pf]

        if None in home_vec:
            print game
            print home_vec
        if None in away_vec:
            print game
            print away_vec

        #print game.home_team,game.away_team
        #print home_stat.to, hst.pts, home_stat.fta, home_stat.oreb
        #print away_stat.to, ast.pts, away_stat.fta, away_stat.oreb

        #home_ppp = hst.pts/float(calc_poss(hst))
        #away_ppp = ast.pts/float(calc_poss(ast))
        #print home_ppp, away_ppp
        #print ''
        #break

    return None
    alpha_raw = np.array([[100,90],[70,80],[60,90]]).T
    beta_raw = np.array([[60,70],[90,90],[100,80]]).T

    alpha_pre = np.array([90,90,90])
    beta_pre = np.array([90,90,90])

    ind_mat = np.array([[2,1],[0,2],[0,1]]).T

    W = np.array([weights(len(alpha_raw[:,k])+1) for k in range(alpha_raw.shape[1])]).T
    #W = np.array([weights(len(alpha_raw[:,k])) for k in range(alpha_raw.shape[1])]).T
    print W
    A0 = np.array([[0, 1, 0], [1, 0, 0], [0, 0, 0]])

    raw_o = np.array([100,90,np.NaN]).T
    raw_d = np.array([90,100,np.NaN]).T

    adj_avg_o_prev = np.array([95,93.2,90]).T
    adj_avg_d_prev = np.array([90,90,100]).T

    o_rank, d_rank = team_rank2(alpha_raw,beta_raw,ind_mat,alpha_pre,beta_pre,W)
    print o_rank, d_rank
    return None
    A1 = np.array([[0, 1, 1], [1, 0, 0], [1, 0, 0]])

    raw_o = np.array([95,90,100]).T
    raw_d = np.array([100,100,88]).T

    o_rank, d_rank = team_rank(o_rank,d_rank,raw_o,raw_d,A1,A1.sum(1))
    print o_rank, d_rank
def calc_poss(bst):
    try:
        poss = xint(bst.fga)+0.475*xint(bst.fta)+xint(bst.to)-xint(bst.oreb)
    except:
        poss = None
    return poss
def xint(num):
    try:
        if num is None:
            return None
        else:
            return int(num)
    except:
        return None
def get_team_box_stats(game):
    bstats = game.box_stats.all()

    home_stat = None
    away_stat = None
    for bst in bstats:
        if is_team_stat(bst):
            if bst.pts == game.home_score:
                home_stat = bst
            elif bst.pts == game.away_score:
                away_stat = bst
            else:
                return None, None
    if home_stat == None or away_stat == None:
        return None, None
    else:
        return home_stat, away_stat
def is_team_stat(box_stat):
    try:
        if box_stat.name != None and box_stat.first_name == None and box_stat.last_name == None:
            return True
        else:
            return False
    except:
        return False
def weights(N,alpha = 0.5):
    w = []
    V = (1-alpha**N)/(1-alpha)
    for i in range(N):
        #w.append(float(i)/sum(range(N)))
        w.append(alpha**i/V)
    w.reverse()
    return w
def team_rank2(alpha_raw,beta_raw, ind_mat, alpha_pre, beta_pre ,W):
    #alpha = 0.2

    #initialize to raw efficiency
    alpha_adj = np.array([np.average(alpha_raw[:,k]) for k in range(alpha_raw.shape[1])])
    beta_adj = np.array([np.average(beta_raw[:,k]) for k in range(beta_raw.shape[1])])

    #alpha_adj_all = st.nanmean(alpha_adj)
    #beta_adj_all = st.nanmean(beta_adj)

    alpha_raw_all = st.nanmean(alpha_adj)
    beta_raw_all = st.nanmean(beta_adj)
    print alpha_raw_all, beta_raw_all

    #print raw_avg_all_o
    #return None
    #print dot(A,gp).T
    cnt = 0
    r_off = 1
    r_def = 1
    while cnt < 10 and not (r_off < 0.001 and r_def < 0.001):


        alpha_adj_prev = alpha_adj
        beta_adj_prev = beta_adj

        #test1 = [sum(np.append(alpha_pre[k],np.multiply(np.true_divide(alpha_raw[:,k],beta_adj_prev[np.array([0,1])]),1))*W[:,k]) for k in range(alpha_raw.shape[1])]
        #print test1
        alpha_adj = [sum(np.append(alpha_pre[k],np.multiply(np.true_divide(alpha_raw[:,k],beta_adj_prev[ind_mat[:,k]]),alpha_raw_all))*W[:,k]) for k in range(alpha_raw.shape[1])]
        #alpha_adj = [sum(np.multiply(np.true_divide(alpha_raw[:,k],beta_adj_prev[ind_mat[:,k]]),alpha_adj_all)*W[:,k]) for k in range(alpha_raw.shape[1])]

        alpha_adj = np.array(alpha_adj)
        #print alpha_adj

        beta_adj = [sum(np.append(beta_pre[k],np.multiply(np.true_divide(beta_raw[:,k],alpha_adj_prev[ind_mat[:,k]]),beta_raw_all))*W[:,k]) for k in range(alpha_raw.shape[1])]
        #beta_adj = [sum(np.multiply(np.true_divide(beta_raw[:,k],alpha_adj_prev[ind_mat[:,k]]),beta_adj_all)*W[:,k]) for k in range(alpha_raw.shape[1])]

        beta_adj = np.array(beta_adj)

        r_off = np.linalg.norm(xnan(alpha_adj_prev - alpha_adj))
        r_def = np.linalg.norm(xnan(beta_adj_prev - beta_adj))
        print alpha_adj, beta_adj
        cnt += 1
    #print adj_avg_o, adj_avg_d
    '''for k in range(len(adj_avg_o)):
        if np.isnan(adj_avg_o[k]):
            adj_avg_o[k] = prev_rank_o[k]
        if np.isnan(adj_avg_d[k]):
            adj_avg_d[k] = prev_rank_d[k]'''
    return alpha_adj, beta_adj
def team_rank(prev_rank_o,prev_rank_d,raw_o,raw_d,A,gp):
    alpha = 0.2

    raw_avg_all_o = st.nanmean(raw_o)
    raw_avg_all_d = st.nanmean(raw_d)

    raw_o = xnan(raw_o)
    raw_d = xnan(raw_d)

    #initialize to raw efficiency
    adj_avg_o = raw_o
    adj_avg_d = raw_d
    #print adj_avg_o

    #print raw_avg_all_o
    #return None
    #print dot(A,gp).T
    cnt = 0
    r_off = 1
    r_def = 1
    while cnt < 100 and not (r_off < 0.001 and r_def < 0.001):
        adj_avg_o_prev = adj_avg_o
        adj_avg_d_prev = adj_avg_d

        adj_avg_o_opp = np.divide(np.dot(A,adj_avg_o_prev),gp)
        adj_avg_d_opp = np.divide(np.dot(A,adj_avg_d_prev),gp)

        '''d_off = np.divide(adj_avg_o_prev,gp)
        d_def = np.divide(adj_avg_d_prev,gp)

        adj_avg_o_opp = np.dot(A,xnan(d_off))
        adj_avg_d_opp = np.dot(A,xnan(d_def))'''
        #print 'adj opp',adj_avg_o_opp, adj_avg_d_opp

        adj_o = raw_avg_all_o*(np.divide(raw_o,adj_avg_d_opp))
        adj_d = raw_avg_all_d*(np.divide(raw_d,adj_avg_o_opp))
        #print 'adj', adj_o, adj_d

        adj_avg_o = prev_rank_o*(1-alpha)+adj_o*alpha
        adj_avg_d = prev_rank_d*(1-alpha)+adj_d*alpha

        r_off = np.linalg.norm(xnan(adj_avg_o_prev - adj_avg_o))
        r_def = np.linalg.norm(xnan(adj_avg_d_prev - adj_avg_d))

        #print r_off, r_def
        #print 'count = %i' % cnt,
        #print adj_avg_o, adj_avg_d

        cnt += 1
    #print adj_avg_o, adj_avg_d
    for k in range(len(adj_avg_o)):
        if np.isnan(adj_avg_o[k]):
            adj_avg_o[k] = prev_rank_o[k]
        if np.isnan(adj_avg_d[k]):
            adj_avg_d[k] = prev_rank_d[k]
    return adj_avg_o, adj_avg_d
def xnan(np_array, new_val = 0):
    np_array[np.isnan(np_array)] = 0

    return np_array
def true_gp(A0,A1):
    gp0 = A0.sum(1).astype(float)
    gp1 = A1.sum(1).astype(float)
    gp_diff = gp1-gp0
    #print gp_diff

    for k in range(len(gp_diff)):
        if gp_diff[k]==0:
            gp1[k] = np.NaN
    return gp1
if __name__ == '__main__':
    main()