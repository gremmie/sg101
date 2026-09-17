"""
Development Django settings.

Each service runs in its own container on the Compose network, so the database
and Redis are reached over TCP; connection details come from the environment
Compose sets (see docker-compose.yml). All config and secrets -- SECRET_KEY, DB
credentials, API keys -- are env vars read by base.py from the environment,
which Compose loads from .env.

Selected by DJANGO_SETTINGS_MODULE, and the default for manage.py and
sg101/celery.py.
"""
import os

from sg101.settings.base import *
from sg101.settings.databases import from_env


# --- Database ----------------------------------------------------------------
# $DB_ENGINE picks the service -- `postgresql` (the `postgres` container) or
# `mysql` (the `db` container, which the snapshot conversion still needs); see
# sg101/settings/databases.py. Credentials come from the environment.
DATABASES = from_env()

# --- Redis / Celery ----------------------------------------------------------
# core/services.py uses a unix socket only when REDIS_UNIX_SOCKET is truthy;
# nulling it falls back to REDIS_HOST/REDIS_PORT.
REDIS_UNIX_SOCKET = None
REDIS_HOST = os.environ.get('REDIS_HOST', 'redis')
REDIS_PORT = int(os.environ.get('REDIS_PORT', '6379'))
REDIS_DB = 0

# db 1 for the broker, keeping the cache (db 2) and the site's kept state (db 0)
# clear of it.
CELERY_BROKER_URL = 'redis://{host}:{port}/1'.format(host=REDIS_HOST, port=REDIS_PORT)

ALLOWED_HOSTS = ['*']

# --- Django Debug Toolbar ----------------------------------------------------
# Unconditional: this module is only ever the development deployment, so there
# is nothing to probe for and nothing to guard against. The toolbar is a dev
# dependency and the prod image does not carry it.
#
# Rebind copies rather than editing in place. `from base import *` binds base's
# own list objects, so `.insert()`/`.append()` here would edit the settings of
# whatever configuration is already live -- and importing this module for its
# LOGGING dict is a thing the suite does. Splicing the toolbar's middleware into
# a process that never registered the app leaves the app registry and
# INSTALLED_APPS disagreeing.
#
# Index 0, which is what the toolbar's docs ask for: "as early as possible in
# the list", the one exception being that it must come after any middleware that
# encodes the response body, such as GZipMiddleware. That exception is also the
# only ordering rule the package enforces (its check_middleware() warns about
# GZip and about nothing else), and this project runs no content-encoding
# middleware -- so adding one later is the thing that would change this answer.
#
# The position depends on RedirectsPanel being off. With it on, the toolbar at
# index 0 answers CommonMiddleware's APPEND_SLASH redirects with a 200
# interstitial instead of passing the 301 through; measured both ways, with the
# panel re-enabled at index 0 as the control. It is also what makes redirect
# monitoring honest: from index 1 the toolbar sits inside CommonMiddleware, so
# an APPEND_SLASH request records as the inner 404 it really is and the 301
# never reaches the panel; from here HistoryPanel records the 301. Application
# redirects record as 302 either way.
MIDDLEWARE = ['debug_toolbar.middleware.DebugToolbarMiddleware'] + list(MIDDLEWARE)
INSTALLED_APPS = INSTALLED_APPS + ['debug_toolbar']
# The toolbar disables RedirectsPanel and ProfilingPanel by default, so an empty
# DISABLE_PANELS does not mean "leave the defaults alone", it means "turn both
# on". ProfilingPanel is wanted, so it stays enabled by omission -- but
# RedirectsPanel is deprecated upstream and slated for removal, and it
# interrupts every dev redirect with an interstitial to do a job HistoryPanel
# now does without one: history keeps the toolbar data for the redirecting
# request, so it can be inspected after the redirect has been followed.
#
# SHOW_TOOLBAR_CALLBACK: the toolbar's own default gates on REMOTE_ADDR being in
# INTERNAL_IPS, and behind Docker's bridge host requests arrive NAT'd from the
# gateway (172.18.0.x), never 127.0.0.1 -- so the toolbar would stay hidden.
# Show it whenever DEBUG is on.
DEBUG_TOOLBAR_CONFIG = {
    'DISABLE_PANELS': {'debug_toolbar.panels.redirects.RedirectsPanel'},
    'SHOW_TOOLBAR_CALLBACK': lambda request: DEBUG,
}

# Logging configuration

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(asctime)s %(levelname)s %(module)s %(process)d %(thread)d %(message)s'
        },
        'simple': {
            'format': '%(asctime)s %(levelname)s %(message)s'
        },
    },
    'filters': {
         'require_debug_false': {
             '()': 'django.utils.log.RequireDebugFalse'
         },
     },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'DEBUG',
            'formatter': 'simple',
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': 'DEBUG',
            'formatter': 'simple',
            'filename': os.path.join(PROJECT_PATH, 'logs', 'sg101.log'),
            'mode': 'a',
            'maxBytes': 100 * 1024,
            'backupCount': 10,
            'encoding': 'utf-8',
        },
        'auth': {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': 'DEBUG',
            'formatter': 'simple',
            'filename': os.path.join(PROJECT_PATH, 'logs', 'auth.log'),
            'mode': 'a',
            'maxBytes': 2 * 1024 * 1024,
            'backupCount': 5,
            'encoding': 'utf-8',
        },
        'search': {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': 'DEBUG',
            'formatter': 'simple',
            'filename': os.path.join(PROJECT_PATH, 'logs', 'search.log'),
            'mode': 'a',
            'maxBytes': 2 * 1024 * 1024,
            'backupCount': 5,
            'encoding': 'utf-8',
        },
        # Every message the site sends, one line each, no bodies. Django's crash
        # mail is not here: AdminEmailHandler sends outside the site's mail
        # wrapper, so error reports are neither categorised nor counted, and a
        # line count of this file undercounts total sends by that many.
        'email': {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': 'DEBUG',
            'formatter': 'simple',
            'filename': os.path.join(PROJECT_PATH, 'logs', 'email.log'),
            'mode': 'a',
            'maxBytes': 2 * 1024 * 1024,
            'backupCount': 5,
            'encoding': 'utf-8',
        },
        # Every Turnstile verification, one line each, plus the submissions
        # that arrive with no token at all. Its own file for the same reason as
        # auth and search: the contact form alone reaches clean() dozens of
        # times a day, and that volume would cut sg101.log's retention by a
        # quarter.
        'turnstile': {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': 'DEBUG',
            'formatter': 'simple',
            'filename': os.path.join(PROJECT_PATH, 'logs', 'turnstile.log'),
            'mode': 'a',
            'maxBytes': 2 * 1024 * 1024,
            'backupCount': 5,
            'encoding': 'utf-8',
        },
        'mail_admins': {
            'class': 'django.utils.log.AdminEmailHandler',
            'level': 'ERROR',
            'formatter': 'simple',
            'filters': ['require_debug_false'],
        },
    },
    'loggers': {
        'django': {
            'level': 'WARNING',
            'propagate': False,
            'handlers': ['file'],
        },
        'auth': {
            'level': 'DEBUG',
            'propagate': False,
            'handlers': ['auth'],
        },
        # propagate: False keeps every executed search out of sg101.log, which
        # the root logger would otherwise collect.
        'search': {
            'level': 'INFO',
            'propagate': False,
            'handlers': ['search'],
        },
        # propagate: True, unlike auth and search. Those two keep their volume
        # out of sg101.log; thirty messages a day is not volume. Every line
        # therefore lands in both files -- successes included, not just
        # failures: a propagated record is offered to each handler up the
        # chain, and the ancestor logger's own level is never re-checked, so
        # root's INFO does not filter it. That is wanted. email.log is the
        # audit trail, and sg101.log is where anyone debugging an incident
        # looks first. Never add mail_admins here: that handler sends email, so
        # an alert about mail failing would fail the same way.
        'email': {
            'level': 'INFO',
            'propagate': True,
            'handlers': ['email'],
        },
        # propagate: False for the same reason as auth and search. Note that
        # it also moves the unavailable WARNING out of sg101.log, because
        # propagation is per-logger and not per-level: an outage leaves its
        # only trace in this file.
        'antispam.turnstile': {
            'level': 'INFO',
            'propagate': False,
            'handlers': ['turnstile'],
        },
        # Markdown logs a DEBUG record per extension as it builds a parser --
        # four of them, and core.markup builds one per render. This entry is
        # what keeps them out of sg101.log, which the root logger below collects
        # at DEBUG.
        'MARKDOWN': {
            'level': 'WARNING',
            'propagate': False,
            'handlers': ['file'],
        },
    },
    'root': {
        'level': 'DEBUG',
        'handlers': ['file'],
    },
}
