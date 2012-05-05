"""
Celery tasks for the POTD app.

"""
from celery.task import task

import potd.tools


@task
def pick_potd():
    potd.tools.pick_potd()
