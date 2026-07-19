"""
This module handles the OAuth integration with Google.

"""
import datetime
import logging
import os

# Temporarily disabled at the Python 3 flip: oauth2client is a deprecated, Py2-era
# library, dropped from the requirements here. gcalendar's OAuth flow will be
# rewritten against the modern google-auth libraries in a later step. Until then
# this module still imports (so the admin imports cleanly) and
# check_credentials_status() -- which only stats a file -- keeps working, but the
# functions that talk to Google raise.
try:
    from oauth2client.client import OAuth2WebServerFlow, FlowExchangeError
    from oauth2client.file import Storage
    _OAUTH2CLIENT_AVAILABLE = True
except ImportError:  # oauth2client not installed on Python 3 yet
    OAuth2WebServerFlow = None
    Storage = None

    class FlowExchangeError(Exception):
        """Placeholder so `except FlowExchangeError` stays valid when the real
        oauth2client isn't installed."""

    _OAUTH2CLIENT_AVAILABLE = False

from django.conf import settings
from django.core.cache import cache


logger = logging.getLogger(__name__)
FLOW_CACHE_KEY = 'gcalendar-oauth-flow'
FLOW_CACHE_TIMEOUT = 60
SCOPE = 'https://www.googleapis.com/auth/calendar'


class OAuthError(Exception):
    """Base exception for errors raised by the oauth module"""


def _require_oauth2client():
    if not _OAUTH2CLIENT_AVAILABLE:
        raise NotImplementedError(
            "Google Calendar OAuth is temporarily disabled: oauth2client is not "
            "available on Python 3. It will be rewritten against google-auth.")


def check_credentials_status():
    """Performs a stat() on the credentials file and returns the last modified
    time as a datetime object. If an error occurs, None is returned.
    """
    try:
        status = os.stat(settings.GCAL_CREDENTIALS_PATH)
    except OSError:
        return None
    return datetime.datetime.fromtimestamp(status.st_mtime)


def get_auth_url(callback_url):
    """
    This function creates an OAuth flow object and uses it to generate an
    authorization URL which is returned to the caller.

    callback_url - a string that is the URL that Google should redirect the user
    to after the user has authorized our application access to their data.

    """
    logger.info("get_auth_url started; callback url='%s'", callback_url)
    _require_oauth2client()

    flow = OAuth2WebServerFlow(client_id=settings.GCAL_CLIENT_ID,
                               client_secret=settings.GCAL_CLIENT_SECRET,
                               scope=SCOPE,
                               redirect_uri=callback_url)

    auth_url = flow.step1_get_authorize_url()
    logger.info("auth url: '%s'", auth_url)

    # Save the flow in the cache so we can use it when Google calls the
    # callback. The expiration time also lets us check to make sure someone
    # isn't spoofing google if we are called at some random time.
    # Note: using the session might seem like a more obvious choice, but flow
    # objects are not JSON-serializable, and we don't want to use pickelable
    # sessions for security reasons.

    cache.set(FLOW_CACHE_KEY, flow, FLOW_CACHE_TIMEOUT)

    return auth_url


def auth_return(request):
    """
    This function should be called after Google has redirected the user
    after the user authorized us. We retrieve the authorization code from the
    request query parameters and then exchange it for access tokens. These
    tokens are stored in our credentials file.

    If an error is encountered, an OAuthError is raised.
    """
    logger.info("auth_return called as '%s'", request.get_full_path())
    _require_oauth2client()

    # Try to retrieve the flow object from the cache
    flow = cache.get(FLOW_CACHE_KEY)
    if not flow:
        logger.warning("auth_return no flow in cache, bailing out")
        raise OAuthError("No flow found. Perhaps we timed out?")

    # Delete flow out of cache to close our operational window
    cache.delete(FLOW_CACHE_KEY)

    # Process the request
    error = request.GET.get('error')
    if error:
        logging.error("auth_return received error: %s", error)
        raise OAuthError("Error authorizing request: %s" % error)

    code = request.GET.get('code')
    if not code:
        logging.error("auth_return missing code")
        raise OAuthError("No authorization code received")

    logging.info("auth_return exchanging code for credentials")
    try:
        credentials = flow.step2_exchange(code)
    except FlowExchangeError as ex:
        logging.error("auth_return exchange failed: %s", ex)
        raise OAuthError(str(ex))

    logging.info("auth_return storing credentials")
    storage = Storage(settings.GCAL_CREDENTIALS_PATH)
    storage.put(credentials)
    logging.info("auth_return completed successfully")


def get_credentials():
    """Obtain the stored credentials if available, or None if they are not."""
    _require_oauth2client()
    storage = Storage(settings.GCAL_CREDENTIALS_PATH)
    return storage.get()
