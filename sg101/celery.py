"""Django / celery integration module."""

from __future__ import absolute_import
import os
import platform
import sys

from celery import Celery
from django.conf import settings

if platform.system() == 'Darwin':
    role = 'mac'
else:
    role = 'production' if platform.node() == 'jaguar' else 'local'

settings_val = 'sg101.settings.{}'.format(role)

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', settings_val)

# Add some stuff to the Python path
sys.path.append('/svr/django-sites/sg101/sg101/tools')

app = Celery('sg101')

app.config_from_object('django.conf:settings')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

# It's useful to have a debug task laying around:

@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))
