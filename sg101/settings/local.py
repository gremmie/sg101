"""
Local Django settings.

"""
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
if DEBUG:
    try:
        import debug_toolbar
    except ImportError:
        pass
    else:
        i = MIDDLEWARE.index('django.middleware.common.CommonMiddleware')
        MIDDLEWARE.insert(i + 1,
                'debug_toolbar.middleware.DebugToolbarMiddleware')
        INSTALLED_APPS.append('debug_toolbar')
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
