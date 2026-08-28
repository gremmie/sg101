"""Server-side verification for Cloudflare Turnstile challenges.

Its own module rather than a function in antispam/utils.py: that module reaches
into bio, comments, forums and user_photos, and this one is imported by two
forms that need none of it. antispam/decorators.py is the same shape.
"""
from dataclasses import dataclass
from enum import StrEnum
import logging

from django.conf import settings
import requests


logger = logging.getLogger(__name__)


class TurnstileOutcome(StrEnum):
    """The result of asking Cloudflare about a token.

    Three values rather than a bool, because a failed challenge and an
    unreachable provider are different events and call for different responses.
    Collapsing them is how an outage becomes "the form rejects everyone" with
    nothing in the log saying why.
    """

    PASSED = 'passed'
    REJECTED = 'rejected'
    # Timeout, connection error, non-200, or a body that is not the JSON the
    # API documents. Nothing was learned about the token.
    UNAVAILABLE = 'unavailable'


@dataclass(frozen=True)
class TurnstileResult:
    """An outcome, plus whatever Cloudflare said about a rejection."""

    outcome: TurnstileOutcome
    error_codes: tuple = ()


def verify(token, remoteip=None):
    """Ask Cloudflare whether a Turnstile token is good.

    Never raises: transport and protocol failures become UNAVAILABLE, so a
    caller decides what an outage means rather than catching exceptions from a
    form's clean() method.
    """
    payload = {
        'secret': settings.TURNSTILE_SECRET_KEY,
        'response': token,
    }
    # Omitted rather than sent as the string "None", which the API would treat
    # as a malformed address.
    if remoteip:
        payload['remoteip'] = remoteip

    try:
        response = requests.post(settings.TURNSTILE_URL, data=payload,
                                 timeout=settings.TURNSTILE_TIMEOUT)
    except requests.RequestException as exc:
        return _unavailable('request failed: %s', exc)

    if response.status_code != 200:
        return _unavailable('unexpected status %s', response.status_code)

    try:
        body = response.json()
    except ValueError as exc:
        return _unavailable('unparseable body: %s', exc)

    if not isinstance(body, dict):
        return _unavailable('unexpected body type: %s', type(body).__name__)

    if body.get('success'):
        logger.info('Turnstile: %s', TurnstileOutcome.PASSED)
        return TurnstileResult(TurnstileOutcome.PASSED)

    codes = tuple(body.get('error-codes') or ())
    logger.info('Turnstile: %s %s', TurnstileOutcome.REJECTED, list(codes))
    return TurnstileResult(TurnstileOutcome.REJECTED, codes)


def _unavailable(msg, *args):
    """Log at WARNING and return UNAVAILABLE.

    WARNING rather than INFO because callers fail open: a passing verification
    and an unchecked one look identical downstream, so this line is the only
    record that the check did not actually happen.
    """
    logger.warning('Turnstile: %s -- ' + msg,
                   TurnstileOutcome.UNAVAILABLE, *args)
    return TurnstileResult(TurnstileOutcome.UNAVAILABLE)
