"""
Email backends for the site.

AllowlistEmailBackend is for a copy of the site with real member data on it,
where mail has to reach the people testing it and nobody else. It is never a
default; a deployment chooses it with EMAIL_BACKEND.

It sits at the backend rather than in core.functions.send_mail because the
backend is the one place every path meets. Django's error mail -- mail_admins,
called by AdminEmailHandler -- never goes through send_mail, and a check there
would also have to be remembered by any path added later that does not either.

"""
import logging
from email.utils import parseaddr

from django.conf import settings
from django.core.mail.backends.smtp import EmailBackend


logger = logging.getLogger('email')

RECIPIENT_FIELDS = ('to', 'cc', 'bcc')


class AllowlistEmailBackend(EmailBackend):
    """
    The SMTP backend, sending only to the addresses in EMAIL_ALLOWLIST.

    Every to, cc and bcc address not on the list is removed and logged, and a
    message left with no recipients is not sent. It fails closed: an empty or
    missing list sends nothing at all.

    """
    def send_messages(self, email_messages):
        allowed = allowlist()
        kept = [message for message in email_messages
                if keep_allowed(message, allowed)]
        if not kept:
            return 0
        return super().send_messages(kept)


def allowlist():
    """The allowed addresses, lowercased, with blank entries left out."""
    entries = getattr(settings, 'EMAIL_ALLOWLIST', None) or ()
    return frozenset(address for address in
                     (entry.strip().lower() for entry in entries) if address)


def keep_allowed(message, allowed):
    """
    Removes message's recipients that are not allowed, logging each one.

    Returns whether anyone is left to send it to. The message is changed in
    place, so what the SMTP backend sends is exactly what this left.

    """
    for field in RECIPIENT_FIELDS:
        kept = []
        for recipient in getattr(message, field):
            if address_of(recipient) in allowed:
                kept.append(recipient)
            else:
                # The same key=value shape as core.tasks.log_send, and like it,
                # no subject: that can be a member's own words.
                logger.info('allowlist dropped field=%s to=%s from=%s',
                            field, recipient, message.from_email)
        setattr(message, field, kept)

    if message.recipients():
        return True

    logger.info('allowlist from=%s outcome=not sent, no allowlisted recipient',
                message.from_email)
    return False


def address_of(recipient):
    """The bare, lowercased address in 'addr' or 'Name <addr>'."""
    return parseaddr(recipient)[1].strip().lower()
