"""
Production Django settings.

"""
import os

from sg101.settings.base import *
from sg101.settings import logging_config
from sg101.settings.databases import from_env

DEBUG = False
SITE_SCHEME = 'https'

ALLOWED_HOSTS = ['.surfguitar101.com']

# The engine and its connection details come from the environment, as they do
# for every other deployment; see sg101/settings/databases.py. Credentials are
# read there from DB_NAME/DB_USER/DB_PASSWORD.
DATABASES = from_env('postgresql')

# Lifetime of the database connections, in seconds:
CONN_MAX_AGE = 1200

# collectstatic writes here during the image build, and WhiteNoise serves out of
# it. Outside the source tree so a collected copy never shadows a source file,
# and inside the image so the manifest cannot disagree with the code it was
# built from.
STATIC_ROOT = os.path.abspath(os.path.join(PROJECT_PATH, '..', 'static_root'))

# WhiteNoise serves the collected files from the application process, directly
# after SecurityMiddleware so that its redirect and headers still apply to
# them. Rebound rather than inserted: `from base import *` binds base's own list
# object, so .insert() here would edit the middleware of whatever configuration
# is already live.
_security, *_rest = MIDDLEWARE
MIDDLEWARE = [_security, 'whitenoise.middleware.WhiteNoiseMiddleware'] + _rest

# Django and the proxy disagree about the scheme unless this is set. There are
# two TLS connections in front of this process -- browser to Cloudflare, and
# Cloudflare to the origin on its own certificate -- and the proxy terminates
# the second one, so the request reaches the application over plain HTTP inside
# the compose network and request.is_secure() would be False without this.
#
# X-Forwarded-Proto is an ordinary request header, so this is only sound while
# the proxy overwrites it rather than passing a client's through, and while
# nothing but the proxy can reach this container.
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

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
# keeps in Redis permanently -- db 0 holds who's-online and the forums'
# latest-post lists, and db 1 is the broker.
# Reached over TCP: each service is its own container, and a unix socket does
# not cross that boundary without bind-mounting a directory into both and
# caring about start order.
REDIS_HOST = os.environ.get('REDIS_HOST', 'redis')
REDIS_PORT = int(os.environ.get('REDIS_PORT', '6379'))

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://{host}:{port}/2'.format(host=REDIS_HOST,
                                                    port=REDIS_PORT),
        'TIMEOUT': 600,
        'KEY_PREFIX': 'sg101',
    },
}
CACHE_MIDDLEWARE_ALIAS = 'default'
CACHE_MIDDLEWARE_SECONDS = 600
CACHE_MIDDLEWARE_KEY_PREFIX = ''

# Only the settings whose defaults differ from base are restated here; the
# rest (host, credentials, TLS, timeout, From addresses) come from the
# environment via base.py, so pointing production at a provider needs no code
# change. EMAIL_HOST is deliberately absent -- base already defaults it to
# localhost, which is what the local relay has always been.
EMAIL_BACKEND = env('EMAIL_BACKEND',
                    default='django.core.mail.backends.smtp.EmailBackend')
EMAIL_PORT = env.int('EMAIL_PORT', default=25)

DONATIONS_DEBUG = False

# Uploads go to S3 again. This was switched to local disk when AWS finished
# deprecating TLS 1.0/1.1 and the Python 2.7 stack could no longer negotiate a
# connection to the bucket; the interpreter is what was broken, and it is not
# any more. Photos already on local disk keep their stored URLs and are served
# from the same path -- nothing is migrated here.
USER_PHOTOS_LOCAL_UPLOAD = False

# SSL related settings
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Logging: shared configuration, with this deployment's differences applied.
LOGGING = logging_config.for_target('production',
                                    log_dir=os.path.join(PROJECT_PATH, 'logs'))
