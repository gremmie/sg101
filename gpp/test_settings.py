"""
Settings to use when running tests. Uses sqlite for speed.
This idea was taken from
http://blog.davidziegler.net/post/370368042/test-database-settings-in-django
"""
from settings import *

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'dev.db',
    },
}
