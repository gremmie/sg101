"""
Build the DATABASES setting from environment variables.

MySQL and PostgreSQL run side by side while the engine migration is in progress,
so the settings modules don't name an engine -- they ask for one. `from_env()`
reads DB_ENGINE ('mysql' or 'postgresql'); host and port default to whichever
Compose service runs that engine, so flipping engines takes one variable and no
other config. DB_HOST/DB_PORT still override, for a database that isn't on the
Compose network. Credentials come from .env (DB_NAME/DB_USER/DB_PASSWORD) as
they have since the 12-factor conversion.

base.py stays engine-agnostic (it defines no DATABASES at all); this module is
imported by the settings that do.
"""
import os

from django.core.exceptions import ImproperlyConfigured


# Per engine: the Django backend, the Compose service that runs it, its port,
# and whatever it needs at connect time.
ENGINES = {
    'mysql': {
        'BACKEND': 'django.db.backends.mysql',
        'HOST': 'db',
        'PORT': '3306',
        # Match the production snapshot's charset (utf8, not utf8mb4) so text
        # renders correctly. The legacy settings set no charset.
        'OPTIONS': {'charset': 'utf8'},
    },
    'postgresql': {
        'BACKEND': 'django.db.backends.postgresql',
        'HOST': 'postgres',
        'PORT': '5432',
        # Nothing to negotiate: the cluster is UTF8 and psycopg2 speaks it.
        'OPTIONS': {},
    },
}


def for_engine(name):
    """Return a DATABASES dict for the named engine, configured from the
    environment. Unknown names fail loudly rather than defaulting."""
    try:
        engine = ENGINES[name]
    except KeyError:
        raise ImproperlyConfigured(
            "Unknown database engine '{}'; expected one of: {}".format(
                name, ', '.join(sorted(ENGINES))))

    return {
        'default': {
            'ENGINE': engine['BACKEND'],
            'NAME': os.environ.get('DB_NAME', 'sg101'),
            'USER': os.environ.get('DB_USER', 'sg101'),
            'PASSWORD': os.environ.get('DB_PASSWORD', 'sg101'),
            'HOST': os.environ.get('DB_HOST', engine['HOST']),
            'PORT': os.environ.get('DB_PORT', engine['PORT']),
            'OPTIONS': dict(engine['OPTIONS']),
        },
    }


def from_env(default='mysql'):
    """Return a DATABASES dict for the engine named by $DB_ENGINE."""
    return for_engine(os.environ.get('DB_ENGINE') or default)
