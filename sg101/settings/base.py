# Base Django settings for the SG101 website.

import json
import os
from decimal import Decimal

from django.contrib.messages import constants as message_constants
from celery.schedules import crontab


PROJECT_PATH = os.path.abspath(os.path.join(os.path.split(__file__)[0], '..'))

DEBUG = True

ADMINS = (
    ('Brian Neal', 'admin@surfguitar101.com'),
)

MANAGERS = ADMINS

INTERNAL_IPS = ['127.0.0.1']

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'America/Chicago'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# Site scheme; http or https.
SITE_SCHEME = 'http'

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = False

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = os.path.abspath(os.path.join(PROJECT_PATH, '..', 'media'))

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = '/media/'

# Staticfiles settings:
STATICFILES_DIRS = [
    os.path.abspath(os.path.join(PROJECT_PATH, '..', 'static')),
    os.path.abspath(os.path.join(PROJECT_PATH, 'static')),
]
STATIC_ROOT = '/tmp/test_static_root'
STATIC_URL = '/static/'

# Make this unique, and don't share it with anybody.
SECRETS = json.load(open(os.path.join(PROJECT_PATH, 'settings', 'secrets.json')))
SECRET_KEY = SECRETS['SECRET_KEY']

MIDDLEWARE_CLASSES = [
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'core.middleware.InactiveUserMiddleware',
    'core.middleware.WhosOnline',
    'wiki.middleware.WikiMiddleware',
    'django.contrib.flatpages.middleware.FlatpageFallbackMiddleware',
]

ROOT_URLCONF = 'sg101.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(PROJECT_PATH, 'templates'),
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                "django.contrib.auth.context_processors.auth",
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.template.context_processors.media",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.admindocs',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.flatpages',
    'django.contrib.humanize',
    'sg101.apps.DjangoMessagesConfig',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.staticfiles',
    'elsewhere',
    'haystack',
    'queued_search',
    'tagging',
    'accounts',
    'antispam',
    'bandmap',
    'banners',
    'bio',
    'bulletins',
    'comments',
    'contact',
    'contests',
    'core',
    'custom_search',
    'donations',
    'downloads',
    'forums',
    'gcalendar',
    'irc',
    'legacy',
    'membermap',
    'messages',
    'news',
    'oembed',
    'podcast',
    'polls',
    'potd',
    'shoutbox',
    'smiley',
    'user_photos',
    'weblinks',
    'wiki',
    'ygroup',
]

LOGIN_URL = 'accounts-login'
LOGIN_REDIRECT_URL = 'bio-me'
LOGOUT_URL = 'accounts-logout'

FILE_UPLOAD_PERMISSIONS = 0644
DEFAULT_FROM_EMAIL = ADMINS[0][1]

#######################################################################
# Messages
#######################################################################
MESSAGE_STORAGE = 'django.contrib.messages.storage.session.SessionStorage'
MESSAGE_TAGS = {
    message_constants.DEBUG: 'notice',
    message_constants.INFO: 'info',
    message_constants.SUCCESS: 'success',
    message_constants.WARNING: 'alert',
    message_constants.ERROR: 'error',
}

#######################################################################
# Email
#######################################################################
EMAIL_HOST = 'localhost'
EMAIL_PORT = 1025
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

#######################################################################
# Sessions
#######################################################################
SESSION_ENGINE = "django.contrib.sessions.backends.cached_db"
SESSION_COOKIE_AGE = 2 * 7 * 24 * 60 * 60   # 2 weeks in seconds
SESSION_COOKIE_DOMAIN = None
SESSION_COOKIE_NAME = 'sg101_sessionid'
SESSION_COOKIE_PATH = '/'
SESSION_COOKIE_SECURE = False
SESSION_EXPIRE_AT_BROWSER_CLOSE = False
SESSION_SAVE_EVERY_REQUEST = False

#######################################################################
# Tagging Specific Settings
#######################################################################
FORCE_LOWERCASE_TAGS = True
MAX_TAG_LENGTH = 50

#######################################################################
# Haystack Search Settings
#######################################################################
HAYSTACK_CONNECTIONS = {
    'default': {
        'ENGINE': 'xapian_backend.XapianEngine',
        'PATH': os.path.join(PROJECT_PATH, 'xapian_index'),
    },
}

#######################################################################
# Redis integration & settings
#######################################################################
REDIS_UNIX_SOCKET = '/var/run/redis/redis.sock'
REDIS_DB = 0

#######################################################################
# Celery integration & settings
#######################################################################
BROKER_URL = 'redis+socket:///var/run/redis/redis.sock?virtual_host=1'
BROKER_POOL_LIMIT = 10
BROKER_TRANSPORT_OPTIONS = {
    'fanout_prefix': True,
    'fanout_patterns': True,
}

CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_SERIALIZER = 'json'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_IGNORE_RESULT = True
# Set this when we want results:
#CELERY_RESULT_BACKEND = 'redis+socket:///var/run/redis/redis.sock?virtual_host=1&new_join=1'
CELERY_DISABLE_RATE_LIMITS = True
CELERY_SEND_TASK_ERROR_EMAILS = True

CELERYBEAT_SCHEDULE = {
    "potd": {
        "task": "potd.tasks.pick_potd",
        "schedule": crontab(minute=0, hour=0),
    },
    "cleanup": {
        "task": "core.tasks.cleanup",
        "schedule": crontab(minute=0, hour=1),
    },
    "purge_messages": {
        "task": "messages.tasks.purge_messages",
        "schedule": crontab(minute=30, hour=1, day_of_week='sunday'),
    },
    "max_users": {
        "task": "core.tasks.max_users",
        "schedule": crontab(minute='*/15'),
    },
    "search_queue": {
        "task": "custom_search.tasks.process_search_queue_task",
        "schedule": crontab(minute='*/20'),
    },
    "expire_wiki_cookies": {
        "task": "wiki.tasks.expire_cookies",
        "schedule": crontab(minute=0, hour=2),
    },
}

#######################################################################
# sg101 Specific Settings
#######################################################################
GPP_NO_REPLY_EMAIL = 'no_reply'
AVATAR_DIR = 'avatars'
MAX_AVATAR_SIZE_BYTES = 2 * 1024 * 1024
MAX_AVATAR_SIZE_PIXELS = 100
AVATAR_DEFAULT_URL = MEDIA_URL + AVATAR_DIR + '/default.png'

# Donations application settings:
DONATIONS_DEBUG = False
DONATIONS_ITEM_NAME = 'Donation for SurfGuitar101.com'
DONATIONS_BUSINESS = 'brian@surfguitar101.com'
DONATIONS_BUSINESS_DEBUG = 'bgneal_1246137628_biz@gmail.com'
DONATIONS_GOAL = Decimal('120.00')  # monthly goal
DONATIONS_ANON_NAME = u'Anonymous'
DONATIONS_ITEM_NUM = '500'          # donation w/name listed
DONATIONS_ITEM_ANON_NUM = '501'     # donation listed as anonymous

# Oembed settings
OEMBED_MAXWIDTH = 480
OEMBED_MAXHEIGHT = 295

# GCalendar settings
GCAL_CALENDAR_ID = 'i81lu3fkh57sgqqenogefd9v78@group.calendar.google.com'

# GCalendar/Google OAuth settings
GCAL_CLIENT_ID = SECRETS['GCAL_CLIENT_ID']
GCAL_CLIENT_SECRET = SECRETS['GCAL_CLIENT_SECRET']
GCAL_CREDENTIALS_PATH = SECRETS['GCAL_CREDENTIALS_PATH']

# MoinMoin Wiki integration settings
WIKI_COOKIE_NAME = 'sg101_wiki'
WIKI_COOKIE_DOMAIN = '.surfguitar101.com'
WIKI_COOKIE_AGE = SESSION_COOKIE_AGE
WIKI_REDIS_SET = 'wiki_cookie_keys'

# User photo upload settings
USER_PHOTOS_ENABLED = True
USER_PHOTOS_ACCESS_KEY = SECRETS['AWS_ACCESS_KEY']
USER_PHOTOS_SECRET_KEY = SECRETS['AWS_SECRET_KEY']
USER_PHOTOS_BUCKET = 'sg101.user.photos'
USER_PHOTOS_BASE_URL = 'https://s3-us-west-1.amazonaws.com'
USER_PHOTOS_MAX_SIZE = (660, 720)
USER_PHOTOS_THUMB_SIZE = (120, 120)
USER_PHOTOS_RATE_LIMIT = (50, 86400)   # number / seconds
HOT_LINK_PHOTOS_BASE_URL = 'https://s3.amazonaws.com/'
HOT_LINK_PHOTOS_BUCKET = 'sg101.forum.photos'

USER_IMAGES_SOURCES = [
    'dl.dropboxusercontent.com',
    's3.amazonaws.com',
    's3-us-west-1.amazonaws.com',
    'scontent-ord1-1.xx.fbcdn.net',
    'lh3.googleusercontent.com',
]

# If this flag is False, the queued_search queue will not be processed. This is
# useful when we are rebuilding the search index.
SEARCH_QUEUE_ENABLED = True

#######################################################################
# Asynchronous settings (queues, queued_search, redis, celery, etc)
#######################################################################
QUEUE_BACKEND = 'redisd'
QUEUE_REDIS_UNIX_SOCKET = REDIS_UNIX_SOCKET
QUEUE_REDIS_DB = 0

#######################################################################
# Open Graph Protocol related settings
#######################################################################
OGP_DEFAULT_IMAGE = SITE_SCHEME + '://surfguitar101.com/media/podcast/podcast_logo.jpg'
OGP_FB_ID = '100001558124013'
OGP_SITE_DESCRIPTION = ('The premier community website for friends and fans of'
    ' instrumental surf music. We have forums, podcasts, surf music news, an'
    ' event calendar, and much more! The surf is always up at'
    ' SurfGuitar101.com!')

#######################################################################
# URL's of 3rd party Javascript and CSS files.
# These dictionaries are used by core/templatetags/script_tags, and
# should also be used by developers when creating form media classes.
GPP_THIRD_PARTY_JS = {
    'imagesloaded': [
        'js/jquery.imagesloaded.min.js',
    ],
    'jquery': [
        'https://ajax.googleapis.com/ajax/libs/jquery/1.11.1/jquery.min.js',
    ],
    'jquery-jeditable': [
        'js/jquery.jeditable.mini.js',
    ],
    'jquery-ui': [
        'https://ajax.googleapis.com/ajax/libs/jqueryui/1.11.0/jquery-ui.min.js',
    ],
    'markitup': [
        'js/markitup/jquery.markitup1.1.14.min.js',
        'js/markitup/sets/markdown/set.js',
    ],
    'tiny_mce': [
        'js/tiny_mce/tiny_mce.js',
        'js/tiny_mce_init_std.js',
    ],
}

GPP_THIRD_PARTY_CSS = {
    'jquery-ui': [
        'https://ajax.googleapis.com/ajax/libs/jqueryui/1.11.0/themes/redmond/jquery-ui.css',
    ],
    'markitup': [
        'js/markitup/skins/markitup/style.css',
        'js/markitup/sets/markdown/style.css',
    ],
}
