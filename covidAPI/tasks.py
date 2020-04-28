from celery import task
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)


@task(name="t1")
def t1():
    print('Task 1 executed')
