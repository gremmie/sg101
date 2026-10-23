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
from sg101.settings import logging_config
from sg101.settings.databases import from_env


# --- Database ----------------------------------------------------------------
# PostgreSQL, the `postgres` container; see sg101/settings/databases.py.
# Credentials come from the environment.
DATABASES = from_env()

# --- Redis / Celery ----------------------------------------------------------
# Host, port, db and the broker URL all come from base.py, which reads the first
# two from the environment and puts the broker on db 1. Nothing to override.

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
# on". Both are named here, matching those defaults:
#
# RedirectsPanel is deprecated upstream and slated for removal, and it
# interrupts every dev redirect with an interstitial to do a job HistoryPanel
# now does without one: history keeps the toolbar data for the redirecting
# request, so it can be inspected after the redirect has been followed.
#
# ProfilingPanel stays on the toolbar, to be switched on for a single page.
# Enabled for every request it breaks concurrent ones -- cProfile allows one
# profiler at a time and runserver is threaded, so a page's parallel /media/
# requests fail with "Another profiling tool is already active" -- and it was
# on when runserver was OOM-killed.
#
# SHOW_TOOLBAR_CALLBACK: the toolbar's own default gates on REMOTE_ADDR being in
# INTERNAL_IPS, and behind Docker's bridge host requests arrive NAT'd from the
# gateway (172.18.0.x), never 127.0.0.1 -- so the toolbar would stay hidden.
# Show it whenever DEBUG is on.
DEBUG_TOOLBAR_CONFIG = {
    'DISABLE_PANELS': {
        'debug_toolbar.panels.profiling.ProfilingPanel',
        'debug_toolbar.panels.redirects.RedirectsPanel',
    },
    'SHOW_TOOLBAR_CALLBACK': lambda request: DEBUG,
}

# Photo uploads go to S3 unless .env says to keep them under MEDIA_ROOT, which
# needs media/user_photos/ to exist.
USER_PHOTOS_LOCAL_UPLOAD = env.bool('USER_PHOTOS_LOCAL_UPLOAD', default=False)

# Logging: shared configuration, with this deployment's differences applied.
LOGGING = logging_config.for_target('dev',
                                    log_dir=os.path.join(PROJECT_PATH, 'logs'))
