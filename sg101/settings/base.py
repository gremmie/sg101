# Base Django settings for the SG101 website.

import json
import os
from decimal import Decimal

from django.contrib.messages import constants as message_constants
import djcelery
from celery.schedules import crontab


PROJECT_PATH = os.path.abspath(os.path.join(os.path.split(__file__)[0], '..'))

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    ('Brian Neal', 'admin@surfguitar101.com'),
)

MANAGERS = ADMINS

AUTH_PROFILE_MODULE = 'bio.userprofile'

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
]
STATIC_ROOT = '/tmp/test_static_root'
STATIC_URL = '/static/'

# Make this unique, and don't share it with anybody.
SECRETS = json.load(open(os.path.join(PROJECT_PATH, 'settings', 'secrets.json')))
SECRET_KEY = SECRETS['SECRET_KEY']

# List of Loader classes that know how to import templates from various sources.

TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
)

MIDDLEWARE_CLASSES = [
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'core.middleware.InactiveUserMiddleware',
    'core.middleware.WhosOnline',
    'wiki.middleware.WikiMiddleware',
    'django.contrib.flatpages.middleware.FlatpageFallbackMiddleware',
]

ROOT_URLCONF = 'sg101.urls'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.join(PROJECT_PATH, 'templates'),
)

TEMPLATE_CONTEXT_PROCESSORS = (
    "django.contrib.auth.context_processors.auth",
    "django.core.context_processors.debug",
    "django.core.context_processors.request",
    "django.core.context_processors.media",
    "django.core.context_processors.static",
    "django.contrib.messages.context_processors.messages",
)

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.admindocs',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.flatpages',
    'django.contrib.humanize',
    'django.contrib.markup',
    'django.contrib.messages',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.staticfiles',
    'djcelery',
    'elsewhere',
    'haystack',
    'queued_search',
    'tagging',
    'accounts',
    'antispam',
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
    'phantombrigade',
    'podcast',
    'polls',
    'potd',
    'shoutbox',
    'smiley',
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
HAYSTACK_SITECONF = 'sg101.search_sites'
HAYSTACK_SEARCH_ENGINE = 'xapian'
HAYSTACK_XAPIAN_PATH = os.path.join(PROJECT_PATH, 'xapian_index')


#######################################################################
# Redis integration & settings
#######################################################################
REDIS_HOST = 'localhost'
REDIS_PORT = 6379
REDIS_DB = 0

#######################################################################
# Celery integration & settings
#######################################################################
BROKER_URL = 'redis://localhost:6379/1'
BROKER_POOL_LIMIT = 10

CELERY_IGNORE_RESULT = True
CELERY_RESULT_BACKEND = 'redis'
CELERY_REDIS_HOST = 'localhost'
CELERY_REDIS_PORT = 6379
CELERY_REDIS_DB = 1

CELERY_DISABLE_RATE_LIMITS = True
CELERY_SEND_TASK_ERROR_EMAILS = True

djcelery.setup_loader()

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
DONATIONS_GOAL = Decimal('100.00')  # monthly goal
DONATIONS_ANON_NAME = u'Anonymous'
DONATIONS_ITEM_NUM = '500'          # donation w/name listed
DONATIONS_ITEM_ANON_NUM = '501'     # donation listed as anonymous

# Oembed settings
OEMBED_MAXWIDTH = 480
OEMBED_MAXHEIGHT = 295

# GCalendar settings
GCAL_CALENDAR_ID = 'i81lu3fkh57sgqqenogefd9v78@group.calendar.google.com'

# Google OAuth settings
GOOGLE_OAUTH_CONSUMER_KEY = 'surfguitar101.com'
GOOGLE_OAUTH_PRIVATE_KEY_PATH = SECRETS['GOOGLE_KEY_PATH']

# Phantom Brigade TeamSpeak3 settings
PB_TS3_IP = '208.77.144.55'
PB_TS3_PORT = 10011
PB_TS3_VID = 17

# MoinMoin Wiki integration settings
WIKI_COOKIE_NAME = 'sg101_wiki'
WIKI_COOKIE_DOMAIN = '.surfguitar101.com'
WIKI_COOKIE_AGE = SESSION_COOKIE_AGE
WIKI_REDIS_SET = 'wiki_cookie_keys'

#######################################################################
# Asynchronous settings (queues, queued_search, redis, celery, etc)
#######################################################################
QUEUE_BACKEND = 'redisd'
QUEUE_REDIS_CONNECTION = 'localhost:6379'
QUEUE_REDIS_DB = 0

#######################################################################
# Open Graph Protocol related settings
#######################################################################
OGP_DEFAULT_IMAGE = 'http://surfguitar101.com/media/podcast/podcast_logo.jpg'
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
        'http://ajax.googleapis.com/ajax/libs/jquery/1.5.2/jquery.min.js',
    ],
    'jquery-jeditable': [
        'js/jquery.jeditable.mini.js',
    ],
    'jquery-ui': [
        'http://ajax.googleapis.com/ajax/libs/jqueryui/1.8.12/jquery-ui.min.js',
    ],
    'markitup': [
        'js/markitup/jquery.markitup.pack.js',
        'js/markitup/sets/markdown/set.js',
    ],
    'tiny_mce': [
        'js/tiny_mce/tiny_mce.js',
        'js/tiny_mce_init_std.js',
    ],
}

GPP_THIRD_PARTY_CSS = {
    'jquery-ui': [
        'http://ajax.googleapis.com/ajax/libs/jqueryui/1.8.12/themes/redmond/jquery-ui.css',
    ],
    'markitup': [
        'js/markitup/skins/markitup/style.css',
        'js/markitup/sets/markdown/style.css',
    ],
}

