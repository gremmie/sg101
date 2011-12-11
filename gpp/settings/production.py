"""
Production Django settings.

"""
from settings.base import *

DEBUG = False

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'gremmies_portal',
        'USER': SECRETS['DB_USER'],
        'PASSWORD': SECRETS['DB_PASSWORD'],
    },
}

# Path to elsewhere application static images
STATICFILES_DIRS.append(('elsewhere',
    '/home/var/django-sites/virtualenvs/sg101/src/django-elsewhere/elsewhere/img'))

STATIC_ROOT = os.path.abspath(os.path.join(PROJECT_PATH, '..', 'static_serve'))

# Used cached template loader
TEMPLATE_LOADERS = [
    ('django.template.loaders.cached.Loader', (
        'django.template.loaders.filesystem.Loader',
        'django.template.loaders.app_directories.Loader',
    )),
]

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION': '127.0.0.1:11211',
        'TIMEOUT': 600,
    },
}
CACHE_MIDDLEWARE_ANONYMOUS_ONLY = True
CACHE_MIDDLEWARE_SECONDS = 600
CACHE_MIDDLEWARE_KEY_PREFIX = ''

EMAIL_HOST = 'localhost'
EMAIL_PORT = 25

GPP_SEND_EMAIL = True
DONATIONS_DEBUG = False

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
        },
    },
    'loggers': {
        'django':{
            'level': 'WARNING',
            'propagate': False,
            'handlers': ['file'],
        },
        'django.request':{
            'level': 'ERROR',
            'propagate': True,
            'handlers': ['mail_admins'],
        },
    },
    'root': {
        'level': 'INFO',
        'handlers': ['file'],
    },
}
