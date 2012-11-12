"""Signal handlers for wiki integration.

"""
import logging

from django.contrib.auth.signals import user_logged_in, user_logged_out

from wiki.constants import SESSION_SET_FLAG, SESSION_SET_MEMBER

logger = logging.getLogger(__name__)


def login_callback(sender, request, user, **kwargs):
    """Signal callback function for a user logging in.

    Sets a flag for the middleware to create an external cookie.

    """
    logger.info('User login: %s', user.username)

    request.session[SESSION_SET_FLAG] = True


def logout_callback(sender, request, user, **kwargs):
    """Signal callback function for a user logging in.

    Sets a flag for the middleware to delete the external cookie.

    Since the user is about to logout, her session will be wiped out after
    this function returns. This forces us to set an attribute on the request
    object so that the response middleware can delete the wiki's cookie.

    """
    logger.info('User logout: %s', user.username)

    # Remember what Redis set member to delete by adding an attribute to the
    # request object:
    request.wiki_delete_cookie = request.session.get(SESSION_SET_MEMBER)


user_logged_in.connect(login_callback, dispatch_uid='wiki.signals.login')
user_logged_out.connect(logout_callback, dispatch_uid='wiki.signals.logout')
