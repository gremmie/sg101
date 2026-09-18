"""
Test tuning shared by every way of running the suite.

Names no database, exactly as base.py names none: the module that runs the tests
picks the engine (see `docker_test`, and `databases.py` for the mapping).
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

# Celery should always execute tasks immediately
CELERY_TASK_ALWAYS_EAGER = True

# Use a different Redis database for tests (the app's own connection; the Celery
# broker's db is the virtual_host on CELERY_BROKER_URL below).
REDIS_DB = 14
# Bare-metal default; docker_test.py overrides this to reach the `redis` service
# over TCP (the only way tests actually run now).
CELERY_BROKER_URL = 'redis+socket:///var/run/redis/redis.sock?virtual_host=15'

# Nothing in the suite collects static, but the staticfiles app is installed and
# a destination keeps it from being the one setting the module leaves undefined.
# The name says what it is; it moved here from base.py, where a value meant for
# tests applied to every deployment.
STATIC_ROOT = '/tmp/test_static_root'

# For unit-testing the Donations module w/o using the Paypal sandbox
DONATIONS_DEBUG_VERIFY_RESPONSE = 'VERIFIED'
DONATIONS_BUSINESS_DEBUG = ['brian@surfguitar101.com']
