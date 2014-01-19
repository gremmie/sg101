"""
Settings to use when running tests. Uses sqlite for speed.

"""
import logging

from sg101.settings.base import *


# Speed up tests:
DEBUG = False
TEMPLATE_DEBUG = False
logging.disable(logging.CRITICAL)
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# Use a different database in Redis for tests
REDIS_DB = 14
QUEUE_REDIS_DB = 14
BROKER_URL = 'redis://localhost:6379/15'
CELERY_REDIS_DB = 15

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'dev.db',
    },
}

# For unit-testing the Donations module w/o using the Paypal sandbox
DONATIONS_DEBUG_VERIFY_RESPONSE = 'VERIFIED'
DONATIONS_BUSINESS_DEBUG = 'brian@surfguitar101.com'
