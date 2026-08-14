# Base Django settings for the SG101 website.

import os
from decimal import Decimal

import environ
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

# Datetimes are stored and manipulated as aware UTC, and rendered in TIME_ZONE
# (or in the viewer's own zone, in the forums). Application code builds them
# with django.utils.timezone.now(), never datetime.now().
#
# No stored value was rewritten to get here. DateTimeField maps to timestamptz
# on PostgreSQL, so the columns already held correct absolute instants: while
# USE_TZ was off Django set the connection's TimeZone to TIME_ZONE and
# PostgreSQL placed each naive value onto the timeline with it. Switching the
# connection to UTC hands the same instants back as aware datetimes.
#
# One thing to know when reading date queries: a lookup like __month has to
# pick a zone before it can decide which calendar month an instant falls in,
# and it uses the *active* timezone. Nothing activates one, so it resolves in
# TIME_ZONE -- but the donations and news rollups pin it explicitly rather than
# depend on that, because an activate() call anywhere would otherwise re-file
# an evening record under the following month with nothing raised.
USE_TZ = True

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# Site scheme; http or https.
SITE_SCHEME = 'http'

# The scheme a form's URLField assumes when a member types a bare domain, which
# is a separate question from SITE_SCHEME above: this one is about links members
# submit to other sites, not about how this site is served.
#
# Django has always prepended http here and changes to https in 6.0; this
# transitional setting takes the new behavior now, so bandmap links and hot-
# linked images land on https rather than on a scheme that mostly redirects.
# It reaches the form fields generated from model URLFields too -- there are 15
# of those across 10 apps, so setting it here is what covers the admin as well.
#
# Setting it raises a RemovedInDjango60Warning by design, announcing its own
# removal once 6.0 makes the behavior unconditional. The deprecation gate
# ignores that one message; the ignore retires with the setting.
FORMS_URLFIELD_ASSUME_HTTPS = True

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

# 12-factor configuration: all secrets/config come from environment variables.
# For local/bare-metal dev a git-ignored .env file at the repo root is loaded
# into the environment; in Docker/CI/prod the vars are already set (Compose's
# env_file, the CI step, or the host), so read_env is a no-op there (it does not
# override existing vars). The path is overridable via DOTENV_PATH -- used by the
# settings boot test to point at a nonexistent file and assert we fail loudly.
env = environ.Env()
env.read_env(os.environ.get('DOTENV_PATH',
                            os.path.join(PROJECT_PATH, '..', '.env')))

# Make this unique, and don't share it with anybody. Required: absent => the app
# refuses to start (ImproperlyConfigured).
SECRET_KEY = env('SECRET_KEY')

MIDDLEWARE = [
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

# Keep implicit primary keys as 32-bit AutoField (the existing schema); without
# this, Django 3.2+ warns (models.W042) and would default new models to
# BigAutoField. Revisiting the width is a deliberate schema decision for later.
DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.admindocs',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.flatpages',
    'django.contrib.humanize',
    'sg101.apps.DjangoMessagesConfig',
    'django.contrib.postgres',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.staticfiles',
    'elsewhere',
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
    'countdown',
    'donations',
    'downloads',
    'forums',
    'gcalendar',
    'messages',
    'news',
    'oembed',
    'podcast',
    'polls',
    'potd',
    'search',
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

FILE_UPLOAD_PERMISSIONS = 0o644
DEFAULT_FROM_EMAIL = ADMINS[0][1]

#######################################################################
# Messages
#######################################################################
MESSAGE_STORAGE = 'django.contrib.messages.storage.session.SessionStorage'
MESSAGE_TAGS = {
    message_constants.DEBUG: 'secondary',
    message_constants.INFO: 'primary',
    message_constants.SUCCESS: 'success',
    message_constants.WARNING: 'warning',
    message_constants.ERROR: 'alert',
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
# Redis integration & settings
#######################################################################
REDIS_UNIX_SOCKET = '/var/run/redis/redis.sock'
REDIS_DB = 0

#######################################################################
# Celery integration & settings
#######################################################################
# Celery reads these via config_from_object(..., namespace='CELERY'): each name
# has its CELERY_ prefix stripped and lowercased to the modern setting (so
# CELERY_BROKER_URL -> broker_url, CELERY_BEAT_SCHEDULE -> beat_schedule, etc.).
CELERY_BROKER_URL = 'redis+socket:///var/run/redis/redis.sock?virtual_host=1'
CELERY_BROKER_POOL_LIMIT = 10
CELERY_BROKER_TRANSPORT_OPTIONS = {
    'fanout_prefix': True,
    'fanout_patterns': True,
}

CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_SERIALIZER = 'json'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_IGNORE_RESULT = True
# Set this when we want results:
#CELERY_RESULT_BACKEND = 'redis+socket:///var/run/redis/redis.sock?virtual_host=1&new_join=1'
CELERY_WORKER_DISABLE_RATE_LIMITS = True

CELERY_BEAT_SCHEDULE = {
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
    "expire_wiki_cookies": {
        "task": "wiki.tasks.expire_cookies",
        "schedule": crontab(minute=0, hour=2),
    },
    # Reports drift between the search index and the models it indexes; repairs
    # nothing. Weekly is generous for a job whose cost is a few seconds, and the
    # interval can be tightened freely if it ever finds anything.
    "reconcile_search_index": {
        "task": "search.tasks.reconcile_index",
        "schedule": crontab(minute=30, hour=3, day_of_week='sunday'),
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
DONATIONS_BUSINESS = ['brian@surfguitar101.com', 'bgneal@gmail.com']
DONATIONS_BUSINESS_DEBUG = ['bgneal_1246137628_biz@gmail.com']
DONATIONS_GOAL = Decimal('94.00')  # monthly goal
DONATIONS_ANON_NAME = u'Anonymous'
DONATIONS_ITEM_NUM = '500'          # donation w/name listed
DONATIONS_ITEM_ANON_NUM = '501'     # donation listed as anonymous

# Oembed settings
OEMBED_MAXWIDTH = 480
OEMBED_MAXHEIGHT = 295

# GCalendar settings
GCAL_CALENDAR_ID = 'i81lu3fkh57sgqqenogefd9v78@group.calendar.google.com'

# GCalendar/Google OAuth settings
GCAL_CLIENT_ID = env('GCAL_CLIENT_ID', default='')
GCAL_CLIENT_SECRET = env('GCAL_CLIENT_SECRET', default='')
GCAL_CREDENTIALS_PATH = env('GCAL_CREDENTIALS_PATH', default='')

# MoinMoin Wiki integration settings
WIKI_COOKIE_NAME = 'sg101_wiki'
WIKI_COOKIE_DOMAIN = '.surfguitar101.com'
WIKI_COOKIE_AGE = SESSION_COOKIE_AGE
WIKI_REDIS_SET = 'wiki_cookie_keys'

# User photo upload settings
USER_PHOTOS_ENABLED = True
USER_PHOTOS_ACCESS_KEY = env('AWS_ACCESS_KEY', default='')
USER_PHOTOS_SECRET_KEY = env('AWS_SECRET_KEY', default='')
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
    'surfguitar101.com',
]

USER_PHOTOS_LOCAL_UPLOAD = False
USER_PHOTOS_LOCAL_UPLOAD_DIR = 'user_photos'

# Google reCAPTCHA settings
RECAPTCHA_URL = 'https://www.google.com/recaptcha/api/siteverify'
RECAPTCHA_SITE_KEY = env('RECAPTCHA_SITE_KEY', default='')
RECAPTCHA_SECRET_KEY = env('RECAPTCHA_SECRET_KEY', default='')

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
