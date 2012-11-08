"""Signal handlers for wiki integration.

"""
import logging

from django.contrib.auth.signals import user_logged_in, user_logged_out


logger = logging.getLogger(__name__)


def login_callback(sender, request, user, **kwargs):
    """Signal callback function for a user logging in.

    Sets a flag for the middleware to create an external cookie.

    """
    logger.info('User login: %s', user.username)

    request.session['wiki_set_cookie'] = True


def logout_callback(sender, request, user, **kwargs):
    """Signal callback function for a user logging in.

    Sets a flag for the middleware to delete the external cookie.

    """
    logger.info('User logout: %s', user.username)

    request.session['wiki_delete_cookie'] = True


user_logged_in.connect(login_callback, dispatch_uid='wiki.signals.login')
user_logged_out.connect(logout_callback, dispatch_uid='wiki.signals.logout')
