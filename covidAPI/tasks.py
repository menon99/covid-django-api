from celery import task
from celery.utils.log import get_task_logger
import os
from analysis.utils import generateCSV,func1

logger = get_task_logger(__name__)


@task()
def t1():
    try:
        generateCSV()
        logger.info('Task 1 executed Boom')
    except FileNotFoundError:
        logger.info('CWD is ' + os.getcwd())

@task()
def t2():
    try:
        func1()
        logger.info('Task 2 Done Boom')
    except FileNotFoundError:
        logger.info('CWD is ' + os.getcwd())
