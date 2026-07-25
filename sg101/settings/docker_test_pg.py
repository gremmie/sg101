"""
Settings for running the test suite against PostgreSQL instead of sqlite.

Identical to `docker_test` in every other respect (eager Celery, fast password
hashing, Redis over TCP) -- only the database differs, so a run of this against a
run of that isolates engine behavior. The engine is forced rather than read from
$DB_ENGINE: this module exists to exercise Postgres specifically.

Which database the suite runs on from here on is a separate decision, made once
the engine migration is finished; until then sqlite remains the default and this
is opt-in.

Run with:  python manage.py test --settings=sg101.settings.docker_test_pg
"""
from sg101.settings.databases import for_engine
from sg101.settings.docker_test import *  # noqa: F401,F403


DATABASES = for_engine('postgresql')
