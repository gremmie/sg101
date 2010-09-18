# Django settings for gpp project.

import os
import platform
from decimal import Decimal
import logging

import local_settings

project_path = os.path.abspath(os.path.split(__file__)[0])

DEBUG = local_settings.DEBUG
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    ('Brian Neal', 'admin@surfguitar101.com'),
)

AUTH_PROFILE_MODULE = 'bio.userprofile'

MANAGERS = ADMINS

DATABASES = local_settings.DATABASES

INTERNAL_IPS = local_settings.INTERNAL_IPS

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = local_settings.TIME_ZONE

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = local_settings.SITE_ID

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = False

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = local_settings.MEDIA_ROOT

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = local_settings.MEDIA_URL

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = local_settings.ADMIN_MEDIA_PREFIX

# Make this unique, and don't share it with anybody.
SECRET_KEY = local_settings.SECRET_KEY

# List of Loader classes that know how to import templates from various sources.

if DEBUG:
    TEMPLATE_LOADERS = (
        'django.template.loaders.filesystem.Loader',
        'django.template.loaders.app_directories.Loader',
    )
else:
    TEMPLATE_LOADERS = (
        ('django.template.loaders.cached.Loader', (
            'django.template.loaders.filesystem.Loader',
            'django.template.loaders.app_directories.Loader',
        )),
    )

if DEBUG:
    MIDDLEWARE_CLASSES = (
        'django.middleware.common.CommonMiddleware',
        'django.middleware.csrf.CsrfViewMiddleware',
        'django.contrib.sessions.middleware.SessionMiddleware',
        'django.contrib.messages.middleware.MessageMiddleware',
        'debug_toolbar.middleware.DebugToolbarMiddleware',
        'django.contrib.auth.middleware.AuthenticationMiddleware',
        'gpp.core.middleware.InactiveUserMiddleware',
        'gpp.core.middleware.WhosOnline',
        'django.contrib.flatpages.middleware.FlatpageFallbackMiddleware',
    )
else:
    MIDDLEWARE_CLASSES = (
        'django.middleware.common.CommonMiddleware',
        'django.middleware.csrf.CsrfViewMiddleware',
        'django.contrib.sessions.middleware.SessionMiddleware',
        'django.contrib.messages.middleware.MessageMiddleware',
        'django.contrib.auth.middleware.AuthenticationMiddleware',
        'gpp.core.middleware.InactiveUserMiddleware',
        'gpp.core.middleware.WhosOnline',
        'django.contrib.flatpages.middleware.FlatpageFallbackMiddleware',
    )

ROOT_URLCONF = 'gpp.urls'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.join(project_path, 'templates'),
    '/home/brian/coding/python/django/django-elsewhere/elsewhere/templates',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    "django.contrib.auth.context_processors.auth",
    "django.core.context_processors.debug",
    "django.core.context_processors.request",
    "django.core.context_processors.media",
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
    'elsewhere',
    'tagging',
    'haystack',
    'accounts',
    'antispam',
    'bio',
    'bulletins',
    'comments',
    'contact',
    'core',
    'donations',
    'downloads',
    'forums',
    'gcalendar',
    'irc',
    'mailer',
    'membermap',
    'messages',
    'news',
    'podcast',
    'polls',
    'potd',
    'shoutbox',
    'smiley',
    'weblinks',
]
if DEBUG:
    INSTALLED_APPS.append('debug_toolbar')

LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/profile/me/'
LOGOUT_URL = '/accounts/logout/'

FILE_UPLOAD_PERMISSIONS = 0644
DEFAULT_FROM_EMAIL = ADMINS[0][1]

#######################################################################
# Messages
#######################################################################
MESSAGE_STORAGE = 'django.contrib.messages.storage.session.SessionStorage'

#######################################################################
# Email
#######################################################################
EMAIL_HOST = local_settings.EMAIL_HOST
EMAIL_PORT = local_settings.EMAIL_PORT

#######################################################################
# Caching
#######################################################################
if local_settings.USE_CACHE:
    CACHE_BACKEND = local_settings.CACHE_BACKEND
    #CACHE_MIDDLEWARE_SECONDS = local_settings.CACHE_MIDDLEWARE_SECONDS
    #CACHE_MIDDLEWARE_KEY_PREFIX = local_settings.CACHE_MIDDLEWARE_KEY_PREFIX
    #CACHE_MIDDLEWARE_ANONYMOUS_ONLY = local_settings.CACHE_MIDDLEWARE_ANONYMOUS_ONLY

#######################################################################
# Sessions
#######################################################################
#SESSION_ENGINE = "django.contrib.sessions.backends.db"
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
HAYSTACK_SITECONF = 'gpp.search_sites'
HAYSTACK_SEARCH_ENGINE = 'xapian'
HAYSTACK_XAPIAN_PATH = os.path.join(project_path, 'xapian_index')


#######################################################################
# GPP Specific Settings
#######################################################################
GPP_LOG_LEVEL = 0
GPP_SEND_EMAIL = local_settings.GPP_SEND_EMAIL  # see MAILER_ENQUEUE_MAIL
GPP_NO_REPLY_EMAIL = 'no_reply'
AVATAR_DIR = 'avatars'
MAX_AVATAR_SIZE_BYTES = 2 * 1024 * 1024
MAX_AVATAR_SIZE_PIXELS = 100
AVATAR_DEFAULT_URL = MEDIA_URL + AVATAR_DIR + '/default.png'

# Donations application settings:
DONATIONS_DEBUG = local_settings.DONATIONS_DEBUG
DONATIONS_ITEM_NAME = 'Donation for SurfGuitar101.com'
DONATIONS_BUSINESS = 'brian@surfguitar101.com'
DONATIONS_BUSINESS_DEBUG = local_settings.DONATIONS_BUSINESS_DEBUG
DONATIONS_GOAL = Decimal('100.00')  # monthly goal
DONATIONS_ANON_NAME = u'Anonymous'
DONATIONS_ITEM_NUM = '500'          # donation w/name listed
DONATIONS_ITEM_ANON_NUM = '501'     # donation listed as anonymous

# If MAILER_ENQUEUE_MAIL is True, all emails will be stored in the
# mailer application's mail queue (database table). It is then expected
# that a daemon or cron job will actually send the mail out. If
# MAILER_ENQUEUE_MAIL is False, then email will only be sent if
# the setting GPP_SEND_EMAIL (above) is True. In any event, emails
# will be logged via the Python logger if the Python logger filter
# DEBUG is active.

MAILER_ENQUEUE_MAIL = True

#######################################################################
# Configure Logging
#######################################################################

logging.basicConfig(
        filename=os.path.join(project_path, 'logs', 'gpp.log'),
        filemode='a',
        format='%(asctime)s %(levelname)s %(message)s',
        level=local_settings.LOG_LEVEL)

#######################################################################
# Django Debug Toolbar 
#######################################################################

if DEBUG:
    DEBUG_TOOLBAR_CONFIG = local_settings.DEBUG_TOOLBAR_CONFIG

#######################################################################
# URL's of 3rd party Javascript and CSS files.
# These dictionaries are used by core/templatetags/script_tags, and
# should also be used by developers when creating form media classes.
GPP_THIRD_PARTY_JS = {
    'jquery': (
        'http://ajax.googleapis.com/ajax/libs/jquery/1.4.2/jquery.min.js',
    ),
    'jquery-jeditable': (
        'js/jquery.jeditable.mini.js',
    ),
    'jquery-ui': (
        'http://ajax.googleapis.com/ajax/libs/jqueryui/1.8.5/jquery-ui.min.js',
    ),
    'markitup': (
        'js/markitup/jquery.markitup.pack.js',
        'js/markitup/sets/markdown/set.js',
    ),
    'tiny_mce': (
        'js/tiny_mce/tiny_mce.js',
        'js/tiny_mce_init_std.js',
    ),
}
GPP_THIRD_PARTY_CSS = {
    'jquery-ui': (
        'http://ajax.googleapis.com/ajax/libs/jqueryui/1.8.5/themes/redmond/jquery-ui.css',
    ),
    'markitup': (
        'js/markitup/skins/markitup/style.css',
        'js/markitup/sets/markdown/style.css',
    ),
}

