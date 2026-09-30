""" receivers.py - Signal receivers for login related events.

We log these events so that fail2ban can perform rate limiting.

"""
import logging

from django.contrib.auth.signals import (user_logged_in, user_logged_out,
        user_login_failed)


# Get the auth logger that is monitored by fail2ban:
logger = logging.getLogger('auth')


def login_callback(sender, request, user, **kwargs):
    """Signal callback function for a user logging in."""
    logger.info('User login signal: %s', user.username)


def logout_callback(sender, request, user, **kwargs):
    """Signal callback function for a user logging in."""

    if user:
        logger.info('User logout signal: %s', user.username)


def login_failed_callback(sender, credentials, **kwargs):
    """Signal callback for a login failure event."""
    logger.error('User login failed signal from %s: %r', sender,
                 credentials.get('username'))


user_logged_in.connect(login_callback, dispatch_uid='antispam.receivers')
user_logged_out.connect(logout_callback, dispatch_uid='antispam.receivers')
user_login_failed.connect(login_failed_callback,
                          dispatch_uid='antispam.receivers')
