"""
Django settings for running the *legacy* stack inside Docker Compose.

This module is intentionally thin: it inherits the unmodified legacy `local`
settings (so the reproduction stays faithful) and
only overrides the two things that differ between "everything on one box talking
over unix sockets" and "each service in its own container talking over the Docker
network (TCP)":

  * the database (a service on the Docker network, not a local unix socket), and
  * Redis / the Celery broker (the `redis` service, not a local unix socket).

Connection details are read from environment variables that docker-compose sets
(see docker-compose.yml). All config/secrets (SECRET_KEY, API credentials, DB
creds) are env vars, loaded by base.py from the environment (Compose's
`env_file: .env`).

Selected via DJANGO_SETTINGS_MODULE=sg101.settings.docker (set in compose).
"""
import os

from sg101.settings.databases import from_env
from sg101.settings.local import *  # noqa: F401,F403


# --- Database: talk to the database service over TCP -------------------------
# The legacy local.py connects to MySQL over a unix socket; inside Compose each
# service is a separate container, so we connect over the network instead.
# $DB_ENGINE picks which service -- `mysql` (the `db` container) or `postgresql`
# (the `postgres` container) -- while the engine migration is in flight; see
# sg101/settings/databases.py. Credentials come from the environment (compose
# initializes both containers with the same ones).
DATABASES = from_env()

# --- Redis / Celery: talk to the `redis` service over TCP --------------------
# core/services.py uses a unix socket only when REDIS_UNIX_SOCKET is truthy;
# nulling it makes it fall back to REDIS_HOST/REDIS_PORT (TCP).
REDIS_UNIX_SOCKET = None
REDIS_HOST = os.environ.get('REDIS_HOST', 'redis')
REDIS_PORT = int(os.environ.get('REDIS_PORT', '6379'))
REDIS_DB = 0

# Celery broker over TCP (db 1 mirrors the legacy virtual_host=1).
CELERY_BROKER_URL = 'redis://{host}:{port}/1'.format(host=REDIS_HOST, port=REDIS_PORT)

ALLOWED_HOSTS = ['*']

# --- Dev-only: make the Django debug toolbar visible inside the container -----
# The toolbar (enabled in local.py under `if DEBUG:`) gates on REMOTE_ADDR being
# in INTERNAL_IPS. Behind Docker's bridge, host requests arrive NAT'd from the
# gateway (172.18.0.x), never 127.0.0.1, so the toolbar stays hidden. Show it
# whenever DEBUG is on. This is dev-only config: it self-disables under
# DEBUG=False, and moves into the dev compose override when the prod/dev split
# lands at the deploy step.
if 'debug_toolbar' in INSTALLED_APPS:
    DEBUG_TOOLBAR_CONFIG = {
        **DEBUG_TOOLBAR_CONFIG,
        'SHOW_TOOLBAR_CALLBACK': lambda request: DEBUG,
    }
