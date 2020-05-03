from django.http import JsonResponse
import os
import pandas as pd
import requests
import json
from .utils import getJsonObject, getIndiaArima, getStateArima, generateGrowthCsv, generateCSV1, generateCSV2
# Create your views here.


def hello(request):

    path = os.getcwd().split('/')
    if path[-1] != 'csv':
        os.chdir('analysis/csv')
    f = open('hello.txt')
    contents = f.read()
    i = int(contents.strip())
    print('cwd is ', os.getcwd())
    obj = {
        'name': 'akash',
        'age': i
    }
    return JsonResponse(obj)


def getState(state):
    p = state.split(' ')

    for i in range(len(p)):
        if p[i] != 'and':
            q = p[i].capitalize()
            p[i] = q

    state = ' '.join(p)
    return state

def processDates(d):
    for i in range(len(d)):
        t1 = d[i].split('-')
        day = t1[2].split(' ')[0]
        month = t1[1]
        year = t1[0]
        d[i] = month + '/' + day + '/' + year
    return d



def getR0(request, state):

    state = getState(state)
    print('state is ', state)

    path = os.getcwd().split('/')
    if path[-1] != 'csv':
        os.chdir('analysis/csv')

    df = pd.read_csv('reproductive_number.csv')
    df.columns = ['date', 'ML', 'Low_90', 'High_90', 'state']

    temp = df[df['state'] == state]

    obj = {}
    obj['date'] = processDates(temp['date'].to_list())
    obj['high'] = temp['High_90'].to_list()
    obj['low'] = temp['Low_90'].to_list()
    obj['ml'] = temp['ML'].to_list()

    return JsonResponse(obj)


def getGrowth(request, state):

    state = getState(state)

    path = os.getcwd().split('/')
    if path[-1] != 'csv':
        os.chdir('analysis/csv')

    df = pd.read_csv('growth.csv')
    t1 = df[df['state'] == state]

    obj = {
        'g1': t1['g1'][t1.index[0]],
        'g2': t1['g2'][t1.index[0]],
        'current': t1['current'][t1.index[0]]
    }

    return JsonResponse(obj)


def getGrowthIndia(request):

    api_url = 'https://api.covid19india.org/data.json'

    jsonObject = getJsonObject(api_url)

    time_series = jsonObject['cases_time_series']

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

    confirmed = []
    dates = []

    for i in time_series:
        c = int(i['totalconfirmed'])
        confirmed.append(c)
        d = i['date'].strip().split(' ')
        date = '2020-' + months[d[1].lower()] + '-' + d[0]
        dates.append(date)

    growth_difference = []

    lockdown1 = '2020-03-25'
    lockdown2 = '2020-04-15'

    for i in range(1, len(confirmed)):
        growth_difference.append(confirmed[i] / confirmed[i-1])
        if i != len(confirmed) - 1 and dates[i + 1] == lockdown1:
            g1 = sum(growth_difference)/len(growth_difference)
        elif i != len(confirmed) - 1 and dates[i + 1] == lockdown2:
            g2 = sum(growth_difference)/len(growth_difference)
    current_growth = sum(growth_difference)/len(growth_difference)

    obj = {
        'g1': g1,
        'g2': g2,
        'current': current_growth
    }
    return JsonResponse(obj)


def indiaArima(request):

    obj = getIndiaArima()
    return JsonResponse(obj)


def stateArima(request, state):

    state = getState(state)
    obj = getStateArima(state)
    return JsonResponse(obj)


def updateR01(request):

    generateCSV1()
    return JsonResponse({'status': 200})

def updateR02(request):
    
    generateCSV2()
    return JsonResponse({'status': 200})


def updateGrowth(request):

    generateGrowthCsv()
    return JsonResponse({'status': 200})
