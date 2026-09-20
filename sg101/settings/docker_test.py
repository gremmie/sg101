"""
Settings for running the test suite inside the Docker container.

The suite runs on PostgreSQL -- the engine the site itself runs on. Testing on a
different engine than production means the tests cannot see anything
engine-specific, and this project has already been bitten by that: the schema an
app builds can drift from the one it runs against without a single test noticing.
Full-text search is Postgres-only besides, so a portable suite could not cover it
at all. The measured price is about two seconds on a seven-second suite.

Inherits the shared test tuning from `test` (eager Celery, fast password hashing,
no logging) and puts the broker on a database of its own.

Run with:  python manage.py test --settings=sg101.settings.docker_test
"""
from sg101.settings.databases import for_engine
from sg101.settings.test import *  # noqa: F401,F403


DATABASES = for_engine('postgresql')


# The suite talks to a real redis -- the `redis` service -- so the
# integration-style tests (who's-online, the forums' latest posts) exercise one
# rather than a mock. Only the broker db differs from base: 15, so a suite run
# cannot consume or discard whatever the development stack has queued on db 1.
CELERY_BROKER_URL = 'redis://{host}:{port}/15'.format(host=REDIS_HOST,
                                                      port=REDIS_PORT)
