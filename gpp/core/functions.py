"""This file houses various core utility functions for GPP"""

import django.core.mail
from django.contrib.sites.models import Site
from django.conf import settings

from core import logging


def send_mail(subject, message, from_email, recipient_list, 
        fail_silently = False, auth_user = None, auth_password = None):
    """The main gpp send email function.
    Use this function to send email from the site. It will obey debug settings and
    log all emails.
    """

    if settings.GPP_SEND_EMAIL:
        django.core.mail.send_mail(subject, message, from_email, recipient_list,
                fail_silently, auth_user, auth_password)

    logging.info('EMAIL:\nFrom: %s\nTo: %s\nSubject: %s\nMessage:\n%s' % 
            (from_email, str(recipient_list), subject, message))


def email_admins(subject, message):
    """Emails the site admins. Goes through the site send_mail function."""
    site = Site.objects.get_current()
    subject = '[%s] %s' % (site.name, subject)
    send_mail(subject, 
            message, 
            '%s@%s' % (settings.GPP_NO_REPLY_EMAIL, site.domain),
            [mail_tuple[1] for mail_tuple in settings.ADMINS])


def email_managers(subject, message):
    """Emails the site managers. Goes through the site send_mail function."""
    site = Site.objects.get_current()
    subject = '[%s] %s' % (site.name, subject)
    send_mail(subject, 
            msg, 
            '%s@%s' % (settings.GPP_NO_REPLY_EMAIL, site.domain),
            [mail_tuple[1] for mail_tuple in settings.MANAGERS])


def get_full_name(user):
    """Returns the user's full name if available, otherwise falls back
    to the username."""
    full_name = user.get_full_name()
    if full_name:
        return full_name
    return user.username

# vim: ts=4 sw=4
