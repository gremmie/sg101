"""Django / celery integration module."""

import os

from celery import Celery
from django.conf import settings

# 12-factor: the settings module comes from the environment (Compose sets
# DJANGO_SETTINGS_MODULE=sg101.settings.docker; a deploy sets its own). Default
# to local for a bare invocation, matching manage.py.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sg101.settings.local')

app = Celery('sg101')

# namespace='CELERY': read only CELERY_-prefixed Django settings (the modern
# lowercase config keys with that prefix), rather than scanning every setting.
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

# It's useful to have a debug task laying around:

@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))
