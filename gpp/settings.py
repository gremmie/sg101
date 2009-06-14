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

DATABASE_ENGINE = local_settings.DATABASE_ENGINE
DATABASE_NAME = local_settings.DATABASE_NAME
DATABASE_USER = local_settings.DATABASE_USER
DATABASE_PASSWORD = local_settings.DATABASE_PASSWORD
DATABASE_HOST = local_settings.DATABASE_HOST
DATABASE_PORT = local_settings.DATABASE_PORT

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

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
#     'django.template.loaders.eggs.load_template_source',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
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
   "django.core.context_processors.auth",
   "django.core.context_processors.debug",
   "django.core.context_processors.request",
   "django.core.context_processors.media"
)

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.admindocs',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.humanize',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.markup',
    'django.contrib.flatpages',
    'elsewhere',
    'tagging',
    'accounts',
    'bio',
    'bulletins',
    'comments',
    'contact',
    'core',
    'donations',
    'downloads',
    'gcalendar',
    'irc',
    'membermap',
    'messages',
    'news',
    'podcast',
    'polls',
    'potd',
    'shoutbox',
    'smiley',
    'weblinks',
)

LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/profile/me/'
LOGOUT_URL = '/accounts/logout/'

FILE_UPLOAD_PERMISSIONS = 0640

#######################################################################
# Caching
#######################################################################
if local_settings.USE_CACHE:
    CACHE_BACKEND = local_settings.CACHE_BACKEND
    #CACHE_MIDDLEWARE_SECONDS = local_settings.CACHE_MIDDLEWARE_SECONDS
    #CACHE_MIDDLEWARE_KEY_PREFIX = local_settings.CACHE_MIDDLEWARE_KEY_PREFIX
    #CACHE_MIDDLEWARE_ANONYMOUS_ONLY = local_settings.CACHE_MIDDLEWARE_ANONYMOUS_ONLY

#######################################################################
# Tagging Specific Settings
#######################################################################
FORCE_LOWERCASE_TAGS = True
MAX_TAG_LENGTH = 50

#######################################################################
# GPP Specific Settings
#######################################################################
GPP_LOG_LEVEL = 0
GPP_SEND_EMAIL = False
GPP_NO_REPLY_EMAIL = 'no_reply'
AVATAR_DIR = 'avatars'
MAX_AVATAR_SIZE_BYTES = 2 * 1024 * 1024
MAX_AVATAR_SIZE_PIXELS = 100
AVATAR_DEFAULT_URL = MEDIA_URL + AVATAR_DIR + '/default.png'

# Donations application settings:
DONATIONS_DEBUG = True
DONATIONS_ITEM_NAME = 'Donation for SurfGuitar101.com'
DONATIONS_BUSINESS = 'brian@surfguitar101.com'
DONATIONS_BUSINESS_DEBUG = 'brian@surfguitar101.com'
DONATIONS_GOAL = Decimal('100.00')  # montly goal
DONATIONS_ANON_NAME = u'Anonymous'
DONATIONS_ITEM_NUM = 500            # donation w/name listed
DONATIONS_ITEM_ANON_NUM = 501       # donation listed as anonymous

#######################################################################
# Configure Logging
#######################################################################

logging.basicConfig(
        filename=os.path.join(project_path, 'logs', 'gpp.log'),
        filemode='a',
        format='%(asctime)s %(levelname)s %(message)s',
        level=local_settings.LOG_LEVEL)


#######################################################################
# URL's of 3rd party Javascript and CSS files.
# These dictionaries are used by core/templatetags/script_tags, and
# should also be used by developers when creating form media classes.
GPP_THIRD_PARTY_JS = {
    'jquery': (
        'http://ajax.googleapis.com/ajax/libs/jquery/1.3.2/jquery.min.js',
    ),
    'jquery-autocomplete': (
        'js/jquery-autocomplete/lib/jquery.bgiframe.min.js',
        'js/jquery-autocomplete/lib/jquery.ajaxQueue.js',
        'js/jquery-autocomplete/jquery.autocomplete.js',
    ),
    'jquery-jeditable': (
        'js/jquery.jeditable.mini.js',
    ),
    'jquery-ui': (
        'http://ajax.googleapis.com/ajax/libs/jqueryui/1.7.1/jquery-ui.min.js',
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
        'http://ajax.googleapis.com/ajax/libs/jqueryui/1.7.1/themes/redmond/jquery-ui.css',
    ),
    'jquery-autocomplete': (
        'js/jquery-autocomplete/jquery.autocomplete.css',
    ),
    'markitup': (
        'js/markitup/skins/markitup/style.css',
        'js/markitup/sets/markdown/style.css',
    ),
}

