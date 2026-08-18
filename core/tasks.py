"""
Celery tasks for the core application.

"""

import logging
import random
import smtplib

import django.core.mail
from celery import shared_task

import core.whos_online


# Named for the subsystem rather than the module, matching the 'auth' and
# 'search' loggers: mail failures belong in the same file as the per-send log,
# not split across two. Until that handler exists this propagates to the root
# logger exactly as a module-named logger would.
logger = logging.getLogger('email')

# Failures that recur identically on every attempt: a recipient the server
# refuses, or a From address it will not accept. Retrying them burns sending
# quota and delays the error reaching a human. Both are *subclasses* of
# SMTPException, so they must be caught ahead of the transient list below --
# reversing the order silently turns every permanent failure into six.
PERMANENT_ERRORS = (
    smtplib.SMTPRecipientsRefused,
    smtplib.SMTPSenderRefused,
    smtplib.SMTPNotSupportedError,
)

# Worth another attempt: the far end refusing the connection, dropping it
# mid-conversation, or answering 4xx. OSError covers the socket-level cases,
# including the timeout EMAIL_TIMEOUT now imposes.
TRANSIENT_ERRORS = (smtplib.SMTPException, OSError)

MAX_RETRIES = 5
RETRY_BACKOFF_BASE = 4
RETRY_BACKOFF_CAP = 600


def _retry_countdown(retries):
    """Exponential backoff with full jitter, in seconds.

    Jitter matters more than it looks: a provider outage fails every queued
    message at once, and an unjittered backoff has them all retry in the same
    instant, repeatedly.
    """
    ceiling = min(RETRY_BACKOFF_BASE * (2 ** retries), RETRY_BACKOFF_CAP)
    return random.uniform(ceiling / 2, ceiling)


@shared_task(bind=True, max_retries=MAX_RETRIES, acks_late=True)
def send_mail(self, **kwargs):
    """
    A task to send mail via Django.

    kwargs must be a dict of keyword arguments for an EmailMessage.

    Retries transient failures. This used to be a bare send with no retry at
    all, which was safe only because the far end was a mail server on
    localhost: it accepted in about a millisecond and then owned delivery,
    queueing and retrying for days on our behalf. Sending through an external
    provider removes that queue, so the durability has to live here instead --
    otherwise a moment's network trouble silently loses a registration
    confirmation.

    acks_late is deliberate. It means a worker killed mid-send will run the
    task again, so a message can go out twice; the alternative loses it. For
    the mail this site sends -- registration confirmations, password resets,
    topic notifications -- a duplicate is a small annoyance and a loss can
    block a signup outright.
    """
    msg = django.core.mail.EmailMessage(**kwargs)
    try:
        msg.send()
    except PERMANENT_ERRORS:
        logger.exception('Permanent failure sending mail; not retrying. '
                         'To: %s Subject: %s',
                         kwargs.get('to'), kwargs.get('subject'))
        raise
    except TRANSIENT_ERRORS as exc:
        if self.request.retries >= self.max_retries:
            # retry() re-raises exc rather than MaxRetriesExceededError, so
            # this is the last chance to say the message was dropped. A
            # silently lost confirmation is the failure this task exists to
            # prevent; if it happens anyway it must be visible.
            logger.error('Giving up sending mail after %d attempts: %s. '
                         'To: %s Subject: %s',
                         self.request.retries + 1, exc,
                         kwargs.get('to'), kwargs.get('subject'))
        raise self.retry(exc=exc,
                         countdown=_retry_countdown(self.request.retries))


@shared_task
def cleanup():
    """
    A task to perform site-wide cleanup actions.

    """
    from django.core.management import call_command

    # Cleanup old sessions

    call_command('clearsessions')

    # Execute our forum cleanup command to delete old last visit records.

    call_command('forum_cleanup')


@shared_task
def max_users():
    """
    Run the periodic task to calculate the who's online max users/visitors
    statistics.

    """
    core.whos_online.max_users()
