web: gunicorn covidAPI.wsgi
worker: python3 manage.py celery worker -B -l info