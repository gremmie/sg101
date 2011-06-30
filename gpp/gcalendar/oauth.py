"""
This module handles the OAuth integration with Google.

"""
from __future__ import with_statement
import logging

import gdata.gauth
from gdata.calendar_resource.client import CalendarResourceClient

from django.conf import settings


logger = logging.getLogger(__name__)
USER_AGENT = 'surfguitar101-gcalendar-v1'
REQ_TOKEN_SESSION_KEY = 'gcalendar oauth request token'


def fetch_auth(request, scopes, callback_url):
    """
    This function fetches a request token from Google and stores it in the
    session. It then returns the authorization URL as a string.

    request - the HttpRequest object for the user requesting the token. The
    token is stored in the session object attached to this request.

    scopes - a list of scope strings that the request token is for. See
    http://code.google.com/apis/gdata/faq.html#AuthScopes

    callback_url - a string that is the URL that Google should redirect the user
    to after the user has authorized our application access to their data.

    This function only supports RSA-SHA1 authentication. Settings in the Django
    settings module determine the consumer key and path to the RSA private key.
    """
    logger.info("fetch_auth started...")
    client = CalendarResourceClient(None, source=USER_AGENT)

    with open(settings.GOOGLE_OAUTH_PRIVATE_KEY_PATH, 'r') as f:
        rsa_key = f.read()
    logger.info("read RSA key; now getting request token")

    request_token = client.GetOAuthToken(
            scopes,
            callback_url,
            settings.GOOGLE_OAUTH_CONSUMER_KEY,
            rsa_private_key=rsa_key)

    logger.info("received token")
    request.session[REQ_TOKEN_SESSION_KEY] = request_token

    auth_url = request_token.generate_authorization_url(google_apps_domain=None)
    logger.info("generated auth url '%s'", str(auth_url))

    return str(auth_url)


def get_access_token(request):
    """
    This function should be called after Google has sent the user back to us
    after the user authorized us. We retrieve the oauth token from the request
    URL and then upgrade it to an access token. We then return the access token.

    """
    logger.info("get_access_token started; retrieving saved request_token...")

    saved_token = request.session.get(REQ_TOKEN_SESSION_KEY)
    if saved_token is None:
        logger.error("saved request token not found in session!")
        return None

    logger.info("extracting token...")
    request_token = gdata.gauth.AuthorizeRequestToken(saved_token,
                        request.build_absolute_uri())

    logger.info("upgrading to access token...")

    client = CalendarResourceClient(None, source=USER_AGENT)
    access_token = client.GetAccessToken(request_token)

    logger.info("upgraded to access token...")
    return access_token
