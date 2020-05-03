from celery import task
from celery.utils.log import get_task_logger
import os
from analysis.utils import generateCSV1, generateGrowthCsv

logger = get_task_logger(__name__)


@task()
def t1():
    try:
        generateCSV1()
        logger.info('Task 1 executed Boom')
    except FileNotFoundError:
        logger.info('CWD is ' + os.getcwd())

@task()
def t3():
    try:
        generateGrowthCsv()
        logger.info('Growth generated')
    except FileNotFoundError:
        logger.info('CWD is ' + os.getcwd())
