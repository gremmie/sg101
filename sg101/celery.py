"""Django / celery integration module."""

from __future__ import absolute_import
import os

from celery import Celery
from django.conf import settings

# 12-factor: the settings module comes from the environment (Compose sets
# DJANGO_SETTINGS_MODULE=sg101.settings.docker; a deploy sets its own). Default
# to local for a bare invocation, matching manage.py.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sg101.settings.local')

app = Celery('sg101')

app.config_from_object('django.conf:settings')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

# It's useful to have a debug task laying around:

@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))
