"""
Local Django settings.

"""
from settings.base import *

DEBUG = True

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': SECRETS['DB_NAME'],
        'USER': SECRETS['DB_USER'],
        'PASSWORD': SECRETS['DB_PASSWORD'],
    },
}

# Django Debug Toolbar support
if DEBUG:
    try:
        import debug_toolbar
    except ImportError:
        pass
    else:
        i = MIDDLEWARE_CLASSES.index('django.middleware.common.CommonMiddleware')
        MIDDLEWARE_CLASSES.insert(i + 1,
                'debug_toolbar.middleware.DebugToolbarMiddleware')
        INSTALLED_APPS.append('debug_toolbar')
        DEBUG_TOOLBAR_CONFIG = {
            'INTERCEPT_REDIRECTS': True,
        }

# Logging configuration

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
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
        },
        'mail_admins': {
            'class': 'django.utils.log.AdminEmailHandler',
            'level': 'ERROR',
            'formatter': 'simple',
            'filters': ['require_debug_false'],
        },
    },
    'loggers': {
        'django':{
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
