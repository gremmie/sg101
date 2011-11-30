"""
Settings to use when running tests. Uses sqlite for speed.

"""
from settings.base import *

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'dev.db',
    },
}

# For unit-testing the Donations module w/o using the Paypal sandbox
DONATIONS_DEBUG_VERIFY_RESPONSE = 'VERIFIED'
DONATIONS_BUSINESS_DEBUG = 'brian@surfguitar101.com'
