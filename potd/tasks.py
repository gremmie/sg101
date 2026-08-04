"""
Celery tasks for the POTD app.

"""

from celery import shared_task

import potd.tools


@shared_task
def pick_potd():
    potd.tools.pick_potd()
