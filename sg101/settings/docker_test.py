"""
Settings for running the test suite inside the Docker container.

Inherits the legacy `test` settings (sqlite database, eager Celery, fast password
hashing) and applies two container-only shims. No product or test code is
changed -- these only reproduce, inside Linux/Docker, the environment the legacy
tests were written against on the Mac.

Run with:  python manage.py test --settings=sg101.settings.docker_test
"""
from django.db.backends.signals import connection_created

from sg101.settings.test import *  # noqa: F401,F403


# --- Shim 1: modern SQLite vs. Django 1.9 ------------------------------------
# The frozen python:2.7 image ships SQLite 3.27, but Django 1.9's SQLite schema
# editor assumes the old ALTER TABLE RENAME semantics (pre-3.25). Without this,
# building the test DB / loading fixtures fails with
# "no such table: <table>__old". PRAGMA legacy_alter_table restores the old
# behavior Django 1.9 expects. (Removed once we climb to a Django that supports
# modern SQLite natively.)
def _sqlite_legacy_alter_table(sender, connection, **kwargs):
    if connection.vendor == 'sqlite':
        connection.cursor().execute('PRAGMA legacy_alter_table = ON;')


connection_created.connect(_sqlite_legacy_alter_table)


# --- Shim 2: point Redis at the `redis` service over TCP ---------------------
# On the Mac the suite talked to a real redis at /tmp/redis.sock; the faithful
# container equivalent is the `redis` service over the network. This lets the
# integration-style tests (who's-online, wiki middleware) exercise a real redis,
# just as they did on the Mac. core/tests/test_services.py was updated to pass
# explicit args rather than depend on these ambient defaults.
import os

REDIS_UNIX_SOCKET = None
REDIS_HOST = os.environ.get('REDIS_HOST', 'redis')
REDIS_PORT = int(os.environ.get('REDIS_PORT', '6379'))
BROKER_URL = 'redis://{host}:{port}/15'.format(host=REDIS_HOST, port=REDIS_PORT)
