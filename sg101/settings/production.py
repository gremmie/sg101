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

# No template-loader block here on purpose. This used to drop APP_DIRS and name
# the cached loader by hand, which Django builds by itself: with no explicit
# `loaders`, it appends the app-directories loader when APP_DIRS is on and wraps
# the result in the cached loader whenever debug is off. DEBUG is False above, so
# the two produce the same chain -- verified equal on 4.2, not assumed. Setting
# `loaders` was also what forced the APP_DIRS deletion, since Django refuses both
# at once.

# Redis, not memcached: Django dropped the python-memcached backend, and the
# host already runs Redis for the Celery broker and for the application data in
# core/services.py, so caching here retires a service rather than replacing one.
# Its own database, because clearing the cache must not touch what the site
# keeps in Redis permanently -- db 0 holds who's-online, the forums' latest-post
# lists and the wiki's cookies, and db 1 is the broker.
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'unix://' + REDIS_UNIX_SOCKET + '?db=2',
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
        # Symmetry with local.py, where this entry does real work. Here it
        # changes nothing: Markdown's per-render chatter is DEBUG and the root
        # logger below is at INFO, so those records are dropped either way.
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
