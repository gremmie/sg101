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
    """What came of a verification attempt.

    Four values rather than a bool, because a failed challenge, an unreachable
    provider and a submission that never carried a token are different events
    and call for different responses. Collapsing them is how an outage becomes
    "the form rejects everyone" with nothing in the log saying why.

    Only the first two describe something Cloudflare said. The other two say
    why it did not, which is the distinction to keep in mind when adding a
    member here.
    """

    PASSED = 'passed'
    REJECTED = 'rejected'
    # Timeout, connection error, non-200, or a body that is not the JSON the
    # API documents. Cloudflare was asked and nothing was learned.
    UNAVAILABLE = 'unavailable'
    # No token to ask about. Cloudflare was never asked, and no request was
    # made -- a submission that never loaded the widget costs nothing.
    NO_TOKEN = 'no token'


@dataclass(frozen=True)
class TurnstileResult:
    """An outcome, plus whatever Cloudflare said about a rejection."""

    outcome: TurnstileOutcome
    error_codes: tuple = ()


def verify(token, remoteip=None, source=None):
    """Ask Cloudflare whether a Turnstile token is good.

    Never raises: transport and protocol failures become UNAVAILABLE, so a
    caller decides what an outage means rather than catching exceptions from a
    form's clean() method.

    An absent token returns NO_TOKEN without calling out. Callers hand theirs
    over unchecked and branch on the result: keeping the test here means a form
    cannot forget it and spend a request on a submission that never loaded the
    widget.

    source names the calling form in the log line. One line per verification
    has been this site's only measure of challenge volume since 2018, and it is
    worth nothing if it cannot say which form was being protected.
    """
    if not token:
        logger.info('Turnstile: %s%s', TurnstileOutcome.NO_TOKEN,
                    _from(source))
        return TurnstileResult(TurnstileOutcome.NO_TOKEN)

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
        return _unavailable(source, 'request failed: %s', exc)

    if response.status_code != 200:
        return _unavailable(source, 'unexpected status %s',
                            response.status_code)

    try:
        body = response.json()
    except ValueError as exc:
        return _unavailable(source, 'unparseable body: %s', exc)

    if not isinstance(body, dict):
        return _unavailable(source, 'unexpected body type: %s',
                            type(body).__name__)

    if body.get('success'):
        logger.info('Turnstile: %s%s', TurnstileOutcome.PASSED,
                    _from(source))
        return TurnstileResult(TurnstileOutcome.PASSED)

    codes = tuple(body.get('error-codes') or ())
    logger.info('Turnstile: %s%s %s', TurnstileOutcome.REJECTED,
                _from(source), list(codes))
    return TurnstileResult(TurnstileOutcome.REJECTED, codes)


def _unavailable(source, msg, *args):
    """Log at WARNING and return UNAVAILABLE.

    WARNING rather than INFO because callers fail open: a passing verification
    and an unchecked one look identical downstream, so this line is the only
    record that the check did not actually happen.
    """
    logger.warning('Turnstile: %s%s -- ' + msg,
                   TurnstileOutcome.UNAVAILABLE, _from(source), *args)
    return TurnstileResult(TurnstileOutcome.UNAVAILABLE)


def _from(source):
    """Render the caller's name as a suffix, or nothing when unnamed."""
    return ' (%s)' % source if source else ''
