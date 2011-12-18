"""This file houses various core utility functions for GPP"""
import datetime
import re
import logging

from django.contrib.sites.models import Site
from django.conf import settings
import django.core.mail

import core.tasks


def send_mail(subject, message, from_email, recipient_list, defer=True, **kwargs):
    """
    The main send email function. Use this function to send email from the
    site. All applications should use this function instead of calling
    Django's directly.
    If defer is True, the email will be sent to a Celery task to actually send
    the email. Otherwise it is sent on the caller's thread. In any event, the
    email will be logged at the DEBUG level.

    """
    # Guard against empty email addresses
    recipient_list = [dest for dest in recipient_list if dest]
    if not recipient_list:
        logging.warning("Empty recipient_list in send_mail")
        return

    logging.debug('EMAIL:\nFrom: %s\nTo: %s\nSubject: %s\nMessage:\n%s',
        from_email, str(recipient_list), subject, message)

    if defer:
        core.tasks.send_mail.delay(subject, message, from_email, recipient_list,
                **kwargs)
    else:
        django.core.mail.send_mail(subject, message, from_email, recipient_list,
                **kwargs)


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


BASE_YEAR = 2010

def copyright_str():
    curr_year = datetime.datetime.now().year
    if curr_year == BASE_YEAR:
        year_range = str(BASE_YEAR)
    else:
        year_range = "%d - %d" % (BASE_YEAR, curr_year)

    return 'Copyright (C) %s, SurfGuitar101.com' % year_range


IP_PAT = re.compile('(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})')

def get_ip(request):
    """Returns the IP from the request or None if it cannot be retrieved."""
    ip = request.META.get('HTTP_X_FORWARDED_FOR',
            request.META.get('REMOTE_ADDR'))

    if ip:
        match = IP_PAT.match(ip)
        ip = match.group(1) if match else None

    return ip


def get_page(qdict):
    """Attempts to retrieve the value for "page" from the given query dict and
    return it as an integer. If the key cannot be found or converted to an
    integer, 1 is returned.
    """
    n = qdict.get('page', 1)
    try:
        n = int(n)
    except ValueError:
        n = 1
    return n
