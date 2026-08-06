"""
Production Django settings.

"""
from sg101.settings.base import *

DEBUG = False
SITE_SCHEME = 'https'

ALLOWED_HOSTS = ['.surfguitar101.com']

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

# Lifetime of the database connections, in seconds:
CONN_MAX_AGE = 1200

STATIC_ROOT = os.path.abspath(os.path.join(PROJECT_PATH, '..', 'static_serve'))

# Both backends are named explicitly even though 'default' is Django's own
# choice: STORAGES replaced a pair of standalone settings, so writing only the
# half that differs would hide where user uploads go. That entry is what moves
# when media goes to object storage.
STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
    'staticfiles': {
        'BACKEND': 'django.contrib.staticfiles.storage.ManifestStaticFilesStorage',
    },
}

# Used cached template loader
del TEMPLATES[0]['APP_DIRS']
TEMPLATES[0]['OPTIONS']['loaders'] = [
    ('django.template.loaders.cached.Loader', (
        'django.template.loaders.filesystem.Loader',
        'django.template.loaders.app_directories.Loader',
    )),
]

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION': 'unix:/var/run/memcached/memcached.sock',
        'TIMEOUT': 600,
        'KEY_PREFIX': 'sg101',
    },
}
CACHE_MIDDLEWARE_ALIAS = 'default'
CACHE_MIDDLEWARE_SECONDS = 600
CACHE_MIDDLEWARE_KEY_PREFIX = ''

EMAIL_HOST = 'localhost'
EMAIL_PORT = 25
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

DONATIONS_DEBUG = False

USER_PHOTOS_LOCAL_UPLOAD = True

# SSL related settings
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

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
            'encoding': 'utf-8',
        },
        'auth': {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': 'INFO',
            'formatter': 'simple',
            'filename': os.path.join(PROJECT_PATH, 'logs', 'auth.log'),
            'mode': 'a',
            'maxBytes': 2 * 1024 * 1024,
            'backupCount': 5,
            'encoding': 'utf-8',
        },
        'search': {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': 'INFO',
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
        'auth': {
            'level': 'INFO',
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
        'level': 'INFO',
        'handlers': ['file'],
    },
}
