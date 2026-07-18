"""
Django settings for running the *legacy* stack inside Docker Compose.

This module is intentionally thin: it inherits the unmodified legacy `local`
settings (so the reproduction stays faithful) and
only overrides the two things that differ between "everything on one box talking
over unix sockets" and "each service in its own container talking over the Docker
network (TCP)":

  * the database host (MySQL is the `db` service, not a local unix socket), and
  * Redis / the Celery broker (the `redis` service, not a local unix socket).

Connection details are read from environment variables that docker-compose sets
(see docker-compose.yml). All config/secrets (SECRET_KEY, API credentials, DB
creds) are env vars, loaded by base.py from the environment (Compose's
`env_file: .env`).

Selected via DJANGO_SETTINGS_MODULE=sg101.settings.docker (set in compose).
"""
import os

from sg101.settings.local import *  # noqa: F401,F403


# --- Database: talk to the `db` service over TCP -----------------------------
# The legacy local.py connects to MySQL over a unix socket; inside Compose each
# service is a separate container, so we connect to the `db` host over the
# network instead. Credentials come from the environment (compose sets these to
# the same values the MySQL container is initialized with).
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.environ.get('DB_NAME', 'sg101'),
        'USER': os.environ.get('DB_USER', 'sg101'),
        'PASSWORD': os.environ.get('DB_PASSWORD', 'sg101'),
        'HOST': os.environ.get('DB_HOST', 'db'),
        'PORT': os.environ.get('DB_PORT', '3306'),
        'OPTIONS': {
            # Match the production snapshot's charset (utf8, not utf8mb4) so
            # text renders correctly. The legacy settings set no charset.
            'charset': 'utf8',
        },
    },
}

# --- Redis / Celery: talk to the `redis` service over TCP --------------------
# core/services.py uses a unix socket only when REDIS_UNIX_SOCKET is truthy;
# nulling it makes it fall back to REDIS_HOST/REDIS_PORT (TCP).
REDIS_UNIX_SOCKET = None
REDIS_HOST = os.environ.get('REDIS_HOST', 'redis')
REDIS_PORT = int(os.environ.get('REDIS_PORT', '6379'))
REDIS_DB = 0

# Celery broker over TCP (db 1 mirrors the legacy virtual_host=1).
BROKER_URL = 'redis://{host}:{port}/1'.format(host=REDIS_HOST, port=REDIS_PORT)

ALLOWED_HOSTS = ['*']
