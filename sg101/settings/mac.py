"""
Local Django settings.

"""
from sg101.settings.base import *
from sg101.settings.local import *

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': SECRETS['DB_NAME'],
        'USER': SECRETS['DB_USER'],
        'PASSWORD': SECRETS['DB_PASSWORD'],
        'OPTIONS': {
            'unix_socket': '/tmp/mysql.sock',
        },
    },
}

REDIS_UNIX_SOCKET = '/tmp/redis.sock'
QUEUE_REDIS_UNIX_SOCKET = REDIS_UNIX_SOCKET
BROKER_URL = 'redis+socket:///tmp/redis.sock?virtual_host=1'
