"""
Settings for running the test suite inside the Docker container.

The suite runs on PostgreSQL -- the engine the site itself runs on. Testing on a
different engine than production means the tests cannot see anything
engine-specific, and this project has already been bitten by that: the schema an
app builds can drift from the one it runs against without a single test noticing.
Full-text search is Postgres-only besides, so a portable suite could not cover it
at all. The measured price is about two seconds on a seven-second suite.

Inherits the shared test tuning from `test` (eager Celery, fast password hashing,
no logging) and adds the container's Redis, which reaches the `redis` service over
TCP rather than the unix socket the bare-metal settings assume.

Run with:  python manage.py test --settings=sg101.settings.docker_test
"""
import os

from sg101.settings.databases import for_engine
from sg101.settings.test import *  # noqa: F401,F403


DATABASES = for_engine('postgresql')


# On the Mac the suite talked to a real redis at /tmp/redis.sock; the faithful
# container equivalent is the `redis` service over the network. This lets the
# integration-style tests (who's-online) exercise a real redis,
# just as they did on the Mac. core/tests/test_services.py was updated to pass
# explicit args rather than depend on these ambient defaults.
REDIS_UNIX_SOCKET = None
REDIS_HOST = os.environ.get('REDIS_HOST', 'redis')
REDIS_PORT = int(os.environ.get('REDIS_PORT', '6379'))
CELERY_BROKER_URL = 'redis://{host}:{port}/15'.format(host=REDIS_HOST, port=REDIS_PORT)
