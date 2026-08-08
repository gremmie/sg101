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
    # The position is load-bearing, despite the toolbar's docs asking to be as
    # early as possible. Middleware at index 0 wraps index 1, so moving this
    # above CommonMiddleware routes ITS responses through the toolbar -- and
    # DISABLE_PANELS is empty below, so RedirectsPanel is live and every
    # APPEND_SLASH redirect turns into a "you are being redirected"
    # interstitial: measured both ways, `/forums` answers 301 from here and 200
    # from index 0. Simplifying this to a prepend silently breaks dev redirects.
    MIDDLEWARE = list(MIDDLEWARE)
    i = MIDDLEWARE.index('django.middleware.common.CommonMiddleware')
    MIDDLEWARE.insert(i + 1,
            'debug_toolbar.middleware.DebugToolbarMiddleware')
    INSTALLED_APPS = INSTALLED_APPS + ['debug_toolbar']
    DEBUG_TOOLBAR_CONFIG = {
        'DISABLE_PANELS': set(),
        'JQUERY_URL': '',
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
