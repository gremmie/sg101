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

# A database of its own for the app's own connection, so a suite run cannot
# disturb the development stack's kept state on db 0. The broker's db is set by
# docker_test, which is the only way the suite runs.
REDIS_DB = 14

# Nothing in the suite collects static, but the staticfiles app is installed and
# a destination keeps it from being the one setting the module leaves undefined.
# The name says what it is; it moved here from base.py, where a value meant for
# tests applied to every deployment.
STATIC_ROOT = '/tmp/test_static_root'

# For unit-testing the Donations module w/o using the Paypal sandbox
DONATIONS_DEBUG_VERIFY_RESPONSE = 'VERIFIED'
DONATIONS_BUSINESS_DEBUG = ['brian@surfguitar101.com']
