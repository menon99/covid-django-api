import os
import json
import requests
import pandas as pd
import numpy as np
from scipy import stats as sps
from scipy import stats as sps
from scipy.interpolate import interp1d

R_T_MAX = 12
r_t_range = np.linspace(0, R_T_MAX, R_T_MAX*100+1)
GAMMA = 1/7

def get_posteriors(sr, sigma=0.15):

    lam = sr[:-1].values * np.exp(GAMMA * (r_t_range[:, None] - 1))

    likelihoods = pd.DataFrame(
        data = sps.poisson.pmf(sr[1:].values, lam),
        index = r_t_range,
        columns = sr.index[1:])
    
    process_matrix = sps.norm(loc=r_t_range,
                              scale=sigma
                             ).pdf(r_t_range[:, None]) 

    process_matrix /= process_matrix.sum(axis=0)
    
    prior0 = np.ones_like(r_t_range)/len(r_t_range)
    prior0 /= prior0.sum()

    posteriors = pd.DataFrame(
        index=r_t_range,
        columns=sr.index,
        data={sr.index[0]: prior0}
    )
    
    log_likelihood = 0.0

    for previous_day, current_day in zip(sr.index[:-1], sr.index[1:]):

        current_prior = process_matrix @ posteriors[previous_day]
        
        numerator = likelihoods[current_day] * current_prior
        denominator = np.sum(numerator)
        
        posteriors[current_day] = numerator/denominator
    
        log_likelihood += np.log(denominator)
    
    return posteriors,log_likelihood

def highest_density_interval(pmf, p=.9, debug=False):

    if(isinstance(pmf, pd.DataFrame)):
        return pd.DataFrame([highest_density_interval(pmf[col], p=p) for col in pmf],
                            index=pmf.columns)
    
    cumsum = np.cumsum(pmf.values)
    
    total_p = cumsum - cumsum[:, None]
    
    lows, highs = (total_p > p).nonzero()
    
    best = (highs - lows).argmin()
    
    low = pmf.index[lows[best]]
    high = pmf.index[highs[best]]
    
    return pd.Series([low, high],
                     index=[f'Low_{p*100:.0f}',
                            f'High_{p*100:.0f}'])

def getR0(state,df_statewise_timeseries):
    
    confirmed = df_statewise_timeseries[df_statewise_timeseries['state'] == state]['confirmed'].to_numpy()

    dates = df_statewise_timeseries[df_statewise_timeseries['state'] == state]['date'].to_numpy()
    dates = pd.to_datetime(dates,infer_datetime_format=True)

    s1 = pd.DataFrame(data={'date' : dates,'confirmed':confirmed})
    s1 = s1.set_index('date')

    smoothed = s1['confirmed'].infer_objects()
    smoothed = smoothed.rename(state + ' cases')

    posteriors, log_likelihood = get_posteriors(smoothed, sigma=.25)

    hdis = highest_density_interval(posteriors, p=.9)
    most_likely = posteriors.idxmax().rename('ML')
    result = pd.concat([most_likely, hdis], axis=1)

    return result


def check_state_name(s):
    if s == 'Telengana':
        return 'Telangana'
    elif s[-1] == '#':
        return s[:-1]
    else:
        return s

def generateCSV():
    
    headers = {'Content-Type': 'application/json'}
    
    api_url = 'https://api.rootnet.in/covid19-in/stats/history'
    
    response = requests.get(api_url, headers=headers)
    
    jsonObject = {}
    
    if response.status_code == 200:
        jsonObject =  json.loads(response.content.decode('utf-8'))
    
    data = jsonObject['data']

    cols = ['date','state','confirmed']
    df_statewise_timeseries = pd.DataFrame(data=None,columns=cols)

    for i in data:
        
        date = i['day']
        regional = i['regional']
        
        for j in regional:
            
            state = check_state_name(j['loc'])
            confirmed = int(j['totalConfirmed']) + 0.0
            df_row = pd.DataFrame(data = [[date,state,confirmed]],columns=cols)
            df_statewise_timeseries = df_statewise_timeseries.append(df_row)
    
    df_final = pd.DataFrame(data = None, columns=['state','ML','Low_90','High_90'])
    
    for i in df_statewise_timeseries['state'].unique():
        r = getR0(i,df_statewise_timeseries)
        r['state'] = [i] * len(r)
        df_final = df_final.append(r)
    
    path = os.getcwd().split('/')
    print('path is ',path)
    if path[-1] != 'csv':
        os.chdir('analysis/csv')

    df_final.to_csv('reproductive_number.csv')

def func1():
    
    path = os.getcwd().split('/')
    if path[-1] != 'csv':
        os.chdir('analysis/csv')
    f = open('hello.txt', 'r')
    contents = f.read()
    i = int(contents.strip())
    w = open('hello.txt', 'w')
    w.write(str(i + 1))