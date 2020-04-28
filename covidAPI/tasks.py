from celery import task
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)


@task()
def t1():
    logger.info('Task 1 executed Boom')

@task()
def t2():
    logger.info('Task 2 Done Boom')