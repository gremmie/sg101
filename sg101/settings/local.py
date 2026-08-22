"""
Local Django settings.

"""
import importlib.util

from sg101.settings.base import *

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': env('DB_NAME'),
        'USER': env('DB_USER'),
        'PASSWORD': env('DB_PASSWORD'),
        'OPTIONS': {
            'unix_socket': '/var/run/mysqld/mysqld.sock',
        },
    },
}

WIKI_COOKIE_DOMAIN = None

# Django Debug Toolbar support
#
# Probe for the package with find_spec rather than importing it: debug-toolbar
# 3.x builds its URLconf (and reads settings) at package-import time, and this
# runs while the settings module is still being constructed -- importing it here
# would re-enter settings loading and blow up. find_spec only locates the module.
if DEBUG and importlib.util.find_spec('debug_toolbar') is not None:
    # Rebind copies rather than editing in place. `from base import *` binds
    # base's own list objects, so `.insert()`/`.append()` here would edit the
    # settings of whatever module is already live -- and importing this one for
    # its LOGGING dict is a thing the suite does. Splicing the toolbar's
    # middleware into a process that never registered the app leaves the app
    # registry and INSTALLED_APPS disagreeing.
    #
    # First, which is what the toolbar's docs ask for: "as early as possible in
    # the list", the one exception being that it must come after any middleware
    # that encodes the response body, such as GZipMiddleware. That exception is
    # also the only ordering rule the package enforces (its check_middleware()
    # warns about GZip and about nothing else), and this project runs no
    # content-encoding middleware -- so adding one later is the thing that would
    # change this answer.
    #
    # It sat after CommonMiddleware for years instead, because middleware at
    # index 0 wraps index 1: from here the toolbar sees CommonMiddleware's
    # responses, and with RedirectsPanel on that turned every APPEND_SLASH
    # redirect into a "you are being redirected" interstitial. Disabling that
    # panel (below) is what freed the position -- measured both ways, and with
    # the panel re-enabled at index 0 to confirm the panel was the cause.
    #
    # The move is also what makes redirect monitoring honest. From index 1 the
    # toolbar is inside CommonMiddleware, so an APPEND_SLASH request records as
    # the inner 404 it really is and the 301 never reaches the panel; from here
    # HistoryPanel records the 301. Application redirects record as 302 either
    # way.
    MIDDLEWARE = ['debug_toolbar.middleware.DebugToolbarMiddleware'] + list(MIDDLEWARE)
    INSTALLED_APPS = INSTALLED_APPS + ['debug_toolbar']
    # The toolbar disables RedirectsPanel and ProfilingPanel by default; an
    # empty DISABLE_PANELS therefore did not mean "leave the defaults alone", it
    # meant "turn both on". ProfilingPanel is wanted, so it stays enabled by
    # omission -- but RedirectsPanel is deprecated upstream and slated for
    # removal, and it interrupts every dev redirect with an interstitial to do a
    # job HistoryPanel now does without one: history keeps the toolbar data for
    # the redirecting request, so it can be inspected after the redirect has
    # been followed.
    DEBUG_TOOLBAR_CONFIG = {
        'DISABLE_PANELS': {'debug_toolbar.panels.redirects.RedirectsPanel'},
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
