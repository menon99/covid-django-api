# Covid19 India API 

#### This API provides the Growth values, ARIMA predictions and R0 values for India.

#### Built using python django and hosted on heroku

#### Base url covid19-api-django.herokuapp.com/

### API endpoints

Endpoint | Function | Example
--- | --- | ---
/growth/india  |   Used to get current growth values for India | Same as endpoint
/growth/(name of state) | Used to get growth values for that state | growth/tamil nadu
/arima/india | Used to get the ARIMA predictions for india | same as endpoint
/arima/(name of state) | Used to get the ARIMA predictions for that state   | arima/kerala
/rnaught/(name of state) | Used to get realtime R0 values for that state | rnaught/maharashtra 

### To run locally, clone the repository and cd into it
```
$ pip3 install -r requirements.txt
$ python3 manage.py runserver
```
#### Visit the endpoints at localhost:8000/

#### Growth values, Arima Predictions and R0 values are updated daily automatically using celery periodic tasks

#### The jupyter notebooks for the above can be viewed at [covid19 india jupyter-notebooks](https://github.com/menon99/covid19-india-jupyter-notebooks)

#### The main website can be viewed at [covid19-india-analysis](https://covid19-india-analysis.herokuapp.com/home)
