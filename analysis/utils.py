import os
import json
import requests
import pandas as pd
import numpy as np
from scipy import stats as sps
from scipy import stats as sps
from scipy.interpolate import interp1d
import datetime
from statsmodels.tsa.arima_model import ARIMA


def getJsonObject(url):

    headers = {'Content-Type': 'application/json'}
    response = requests.get(url, headers=headers)
    jsonObject = {}
    if response.status_code == 200:
        jsonObject = json.loads(response.content.decode('utf-8'))
    return jsonObject


R_T_MAX = 12
r_t_range = np.linspace(0, R_T_MAX, R_T_MAX*100+1)
GAMMA = 1/7

month_abbr = {
    'Mar': '03',
    'Apr': '04',
    'May': '05',
    'Jun': '06',
}

months = {
    'january': '01',
    'february': '02',
    'march': '03',
    'april': '04',
    'may': '05',
    'june': '06',
    'july': '07',
    'august': '08',
    'september': '09',
    'october': '10',
    'november': '11',
    'december': '12'
}


def get_posteriors(sr, sigma=0.15):

    lam = sr[:-1].values * np.exp(GAMMA * (r_t_range[:, None] - 1))

    likelihoods = pd.DataFrame(
        data=sps.poisson.pmf(sr[1:].values, lam),
        index=r_t_range,
        columns=sr.index[1:])

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

    return posteriors, log_likelihood


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


def getR0(state, df_statewise_timeseries):

    confirmed = df_statewise_timeseries[df_statewise_timeseries['state']
                                        == state]['confirmed'].to_numpy()

    dates = df_statewise_timeseries[df_statewise_timeseries['state']
                                    == state]['date'].to_numpy()
    dates = pd.to_datetime(dates, infer_datetime_format=True)

    s1 = pd.DataFrame(data={'date': dates, 'confirmed': confirmed})
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

    api_url = 'https://api.rootnet.in/covid19-in/stats/history'
    jsonObject = getJsonObject(api_url)

    data = jsonObject['data']

    cols = ['date', 'state', 'confirmed']
    df_statewise_timeseries = pd.DataFrame(data=None, columns=cols)

    for i in data:

        date = i['day']
        regional = i['regional']

        for j in regional:

            state = check_state_name(j['loc'])
            confirmed = int(j['totalConfirmed']) + 0.0
            df_row = pd.DataFrame(
                data=[[date, state, confirmed]], columns=cols)
            df_statewise_timeseries = df_statewise_timeseries.append(df_row)

    df_final = pd.DataFrame(
        data=None, columns=['state', 'ML', 'Low_90', 'High_90'])

    for i in df_statewise_timeseries['state'].unique():
        r = getR0(i, df_statewise_timeseries)
        r['state'] = [i] * len(r)
        df_final = df_final.append(r)

    path = os.getcwd().split('/')
    print('path is ', path)
    if path[-1] != 'csv':
        os.chdir('analysis/csv')

    df_final.to_csv('reproductive_number.csv')

##########################################################


def getGrowth(state, confirmed, dates):

    growth_difference = []

    lockdown1 = '2020-03-25'
    lockdown2 = '2020-04-15'

    g1, g2, current_growth = 0, 0, 0

    for i in range(1, len(confirmed)):
        growth_difference.append(confirmed[i] / confirmed[i-1])
        if i != len(confirmed) - 1 and dates[i + 1] == lockdown1:
            g1 = sum(growth_difference)/len(growth_difference)
        elif i != len(confirmed) - 1 and dates[i + 1] == lockdown2:
            g2 = sum(growth_difference)/len(growth_difference)

    current_growth = sum(growth_difference)/len(growth_difference)

    df = pd.DataFrame(data=[[round(g1, 3), round(g2, 3), round(current_growth, 3), state]], columns=[
                      'g1', 'g2', 'current', 'state'])
    return df


def getDate(s):

    parts = s.split('-')
    date = '2020-' + month_abbr[parts[1]] + '-' + parts[0]
    return date

def getDate2(s):

    parts = s.split('-')
    date = month_abbr[parts[1]] + '/' + parts[0] + '/2020'
    return date

def generateGrowthCsv():

    url = 'https://api.covid19india.org/data.json'
    jsonObject = getJsonObject(url)

    time_series = jsonObject['cases_time_series']

    confirmed = []
    dates = []

    for i in time_series:
        c = int(i['totalconfirmed'])
        confirmed.append(c)
        d = i['date'].strip().split(' ')
        date = '2020-' + months[d[1].lower()] + '-' + d[0]
        dates.append(date)

    df = pd.DataFrame(data=None, columns=['g1', 'g2', 'current', 'state'])

    df.append(getGrowth('India', confirmed, dates))

    url = 'https://api.covid19india.org/v2/state_district_wise.json'
    jsonObject = getJsonObject(url)

    state_mapping = {}
    state_truth = {}
    state_growth = {}

    for i in jsonObject:
        state = i['state']
        code = i['statecode'].lower()
        state_mapping[code] = state
        state_truth[code] = False
        state_growth[state] = {
            'dates': [],
            'cases': []
        }

    url = 'https://api.covid19india.org/states_daily.json'
    jsonObject = getJsonObject(url)

    states_daily = jsonObject['states_daily']

    for i in states_daily:
        if i['status'] == 'Confirmed':
            date = getDate(i['date'])
            del i['date']
            del i['status']
            del i['tt']
            for state in i.keys():
                try:
                    if int(i[state]) > 0 or state_truth[state]:
                        state_truth[state] = True
                        sf = state_mapping[state]
                        state_growth[sf]['dates'].append(date)
                        if len(state_growth[sf]['cases']) != 0:
                            state_growth[sf]['cases'].append(
                                int(i[state]) + state_growth[sf]['cases'][-1])
                        else:
                            state_growth[sf]['cases'].append(int(i[state]))
                except ValueError:
                    continue
                except KeyError:
                    continue
        else:
            continue

    for state in state_growth.keys():
        confirmed = state_growth[state]['cases']
        dates = state_growth[state]['dates']
        df = df.append(getGrowth(state, confirmed, dates))

    path = os.getcwd().split('/')
    print('path is ', path)
    if path[-1] != 'csv':
        os.chdir('analysis/csv')

    df.to_csv('growth.csv')

##########################################################


def getArima(confirmed, datetime_series):

    print('confirmed is ', confirmed)
    start_date = datetime_series.max()
    td = datetime.datetime.today() - start_date

    try:
        arima = ARIMA(confirmed, order=(5, 1, 0))
        arima = arima.fit(trend='c', full_output=True,
                          disp=True, transparams=False)
        forecast = arima.forecast(steps=(td.days + 10))
        pred = list(forecast[0])
    except:
        pred = [confirmed[-1]] * (td.days + 10)

    return pred


def getDates(l, start_date):

    format = "%m/%d/%Y"
    prediction_dates = []

    for i in range(l):
        date = start_date + datetime.timedelta(days=1)
        prediction_dates.append(date.strftime(format))
        start_date = date

    return prediction_dates


def getIndiaArima():

    api_url = 'https://api.covid19india.org/data.json'
    jsonObject = getJsonObject(api_url)

    time_series = jsonObject['cases_time_series']

    confirmed = []
    dates = []
    dates2 = []

    for i in time_series:
        c = int(i['totalconfirmed'])
        confirmed.append(c)
        d = i['date'].strip().split(' ')
        date = '2020-' + months[d[1].lower()] + '-' + d[0]
        dates.append(date)
        date = months[d[1].lower()] + '/' + d[0] + '/2020'
        dates2.append(date)

    datetime_series = pd.to_datetime(dates, infer_datetime_format=True)

    l1 = datetime.datetime(2020, 3, 25)
    l2 = datetime.datetime(2020, 4, 14)

    pred_before = getArima(confirmed[0:55], datetime_series[0:55])
    dates_before = getDates(len(pred_before), l1)

    pred_l1 = getArima(confirmed[0:75], datetime_series[0:75])
    dates_l1 = getDates(len(pred_l1), l2)

    pred_l2 = getArima(confirmed, datetime_series)
    dates_l2 = getDates(len(pred_l2), datetime_series.max())


    obj = {
        'pb': pred_before,
        'db': dates_before,
        'p1': pred_l1,
        'd1': dates_l1,
        'p2': pred_l2,
        'd2': dates_l2,
        'actual' : confirmed,
        'dates' : dates2
    }

    return obj

###########################################################

def getStateArima(state):

    temp_state = state.lower()

    api_url = 'https://api.covid19india.org/v2/state_district_wise.json'
    jsonObject = getJsonObject(api_url)

    state_code = ''

    for i in jsonObject:

        if i['state'].lower() == temp_state:
            state_code = i['statecode'].lower()
            break

    confirmed = []
    dates = []
    dates2 = []

    api_url = 'https://api.covid19india.org/states_daily.json'
    jsonObject = getJsonObject(api_url)
    states_daily = jsonObject['states_daily']

    flag = False

    for i in states_daily:
        if (int(i[state_code]) > 0 or flag) and i['status'] == 'Confirmed':
            flag = True
            dates.append(getDate(i['date']))
            dates2.append(getDate2(i['date']))
            if len(confirmed) > 0:
                confirmed.append(confirmed[-1] + int(i[state_code]))
            else:
                confirmed.append(int(i[state_code]))

    datetime_series = pd.to_datetime(dates, infer_datetime_format=True)

    pred = getArima(confirmed, datetime_series)
    dpred = getDates(len(pred), datetime_series.max())

    obj = {
        'pred' : pred,
        'dp' : dpred,
        'actual' : confirmed,
        'dates' : dates2
    }

    return obj

###############################################################

def func1():

    path = os.getcwd().split('/')
    if path[-1] != 'csv':
        os.chdir('analysis/csv')
    f = open('hello.txt', 'r')
    contents = f.read()
    i = int(contents.strip())
    w = open('hello.txt', 'w')
    w.write(str(i + 1))
