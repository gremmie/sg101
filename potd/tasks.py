"""
Celery tasks for the POTD app.

"""
from __future__ import absolute_import

from celery import shared_task

import potd.tools


@shared_task
def pick_potd():
    potd.tools.pick_potd()
