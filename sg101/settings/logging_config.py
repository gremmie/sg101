"""
Build the LOGGING setting for a deployment target.

The two deployments want the same logging with four differences, so the dicts
are built here rather than written out per module: they ran to ~145 lines each,
and adding a logger meant editing both identically, with nothing to catch it
when only one was edited.

Everything not in TARGETS below is shared by construction. What differs:

  * how verbose the four app log files are, and the `auth` logger feeding one
    of them -- DEBUG while developing, INFO in production
  * the root logger's level, for the same reason
  * disable_existing_loggers
  * whether request errors are mailed to the admins

`log_dir` is a parameter rather than read from the settings: these dicts name
files, and importing a settings module to find out where would make this one a
settings module too.

base.py defines no LOGGING at all, exactly as it defines no DATABASES; the
modules that deploy are the ones that ask (see databases.py, same shape).
"""
import os

from django.core.exceptions import ImproperlyConfigured


# Per target, the only things the two deployments disagree about.
TARGETS = {
    'dev': {
        # Left False so a library that configured its own logger before this
        # dict is applied keeps working -- convenient while developing, and the
        # reason the two targets differ here at all.
        'disable_existing_loggers': False,
        'app_log_level': 'DEBUG',
        'root_level': 'DEBUG',
        'mail_request_errors': False,
    },
    'production': {
        'disable_existing_loggers': True,
        'app_log_level': 'INFO',
        'root_level': 'INFO',
        'mail_request_errors': True,
    },
}

# The four application log files. Each gets its own handler at app_log_level,
# and each rotates at 2 MB rather than sg101.log's 100 KB.
APP_LOGS = ('auth', 'search', 'email', 'turnstile')


def _rotating_file(filename, level, max_bytes, backup_count):
    return {
        'class': 'logging.handlers.RotatingFileHandler',
        'level': level,
        'formatter': 'simple',
        'filename': filename,
        'mode': 'a',
        'maxBytes': max_bytes,
        'backupCount': backup_count,
        'encoding': 'utf-8',
    }


def for_target(name, log_dir):
    """Return a LOGGING dict for the named target, writing files to log_dir.

    Unknown names fail loudly rather than defaulting.
    """
    try:
        target = TARGETS[name]
    except KeyError:
        raise ImproperlyConfigured(
            "Unknown logging target '{}'; expected one of: {}".format(
                name, ', '.join(sorted(TARGETS))))

    app_level = target['app_log_level']

    handlers = {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'DEBUG',
            'formatter': 'simple',
        },
        # The site log. Its own level stays at DEBUG in both targets; what it
        # actually collects is decided by the root logger's level below.
        'file': _rotating_file(os.path.join(log_dir, 'sg101.log'),
                               'DEBUG', 100 * 1024, 10),
        'mail_admins': {
            'class': 'django.utils.log.AdminEmailHandler',
            'level': 'ERROR',
            'formatter': 'simple',
            'filters': ['require_debug_false'],
        },
    }
    for app_log in APP_LOGS:
        handlers[app_log] = _rotating_file(
            os.path.join(log_dir, '{}.log'.format(app_log)),
            app_level, 2 * 1024 * 1024, 5)

    loggers = {
        'django': {
            'level': 'WARNING',
            'propagate': False,
            'handlers': ['file'],
        },
        'auth': {
            'level': app_level,
            'propagate': False,
            'handlers': ['auth'],
        },
        # propagate: False keeps every executed search out of sg101.log, which
        # the root logger would otherwise collect.
        'search': {
            'level': 'INFO',
            'propagate': False,
            'handlers': ['search'],
        },
        # propagate: True, unlike auth and search. Those two keep their volume
        # out of sg101.log; thirty messages a day is not volume. Every line
        # therefore lands in both files -- successes included, not just
        # failures: a propagated record is offered to each handler up the
        # chain, and the ancestor logger's own level is never re-checked, so
        # root's INFO does not filter it. That is wanted. email.log is the
        # audit trail, and sg101.log is where anyone debugging an incident
        # looks first. Never add mail_admins here: that handler sends email, so
        # an alert about mail failing would fail the same way.
        'email': {
            'level': 'INFO',
            'propagate': True,
            'handlers': ['email'],
        },
        # propagate: False for the same reason as auth and search. Note that
        # it also moves the unavailable WARNING out of sg101.log, because
        # propagation is per-logger and not per-level: an outage leaves its
        # only trace in this file.
        'antispam.turnstile': {
            'level': 'INFO',
            'propagate': False,
            'handlers': ['turnstile'],
        },
        # Markdown logs a DEBUG record per extension as it builds a parser --
        # four of them, and core.markup builds one per render. This entry keeps
        # them out of sg101.log wherever the root logger runs at DEBUG; where it
        # runs at INFO the records are dropped either way and this changes
        # nothing.
        'MARKDOWN': {
            'level': 'WARNING',
            'propagate': False,
            'handlers': ['file'],
        },
    }

    if target['mail_request_errors']:
        # Django's own crash mail. propagate stays True so the record still
        # reaches the root logger and sg101.log.
        loggers['django.request'] = {
            'level': 'ERROR',
            'propagate': True,
            'handlers': ['mail_admins'],
        }

    return {
        'version': 1,
        'disable_existing_loggers': target['disable_existing_loggers'],
        'formatters': {
            'verbose': {
                'format': '%(asctime)s %(levelname)s %(module)s %(process)d %(thread)d %(message)s'
            },
            'simple': {
                'format': '%(asctime)s %(levelname)s %(message)s'
            },
        },
        'filters': {
            'require_debug_false': {
                '()': 'django.utils.log.RequireDebugFalse'
            },
        },
        'handlers': handlers,
        'loggers': loggers,
        'root': {
            'level': target['root_level'],
            'handlers': ['file'],
        },
    }
