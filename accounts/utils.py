import logging
import secrets

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone

from core.email_categories import EmailCategory
from core.functions import send_mail


logger = logging.getLogger('auth')

# Bytes of randomness behind a confirmation token; 32 yields 43 URL-safe
# characters, which the 64-character PendingUser.key column holds with room to
# grow.
TOKEN_NBYTES = 32


def make_confirmation_token():
    """
    Return a URL-safe one-time token drawn from the system CSPRNG.

    Shared by every flow that emails a confirmation link, so that none of them
    has to decide how to generate one.

    """
    return secrets.token_urlsafe(TOKEN_NBYTES)


def create_new_user(pending_user, ip=None, admin_activation=False):
    """
    This function contains the code to create a new user from a
    pending user. The pending user is deleted and the new user
    is saved. A log message is produced. If admin_activation is false,
    then ip should be the user's IP they confirmed from, if available.

    """
    new_user = User()

    new_user.username = pending_user.username
    new_user.first_name = ''
    new_user.last_name = ''
    new_user.email = pending_user.email
    new_user.password = pending_user.password     # already been hashed
    new_user.is_staff = False
    new_user.is_active = True
    new_user.is_superuser = False
    new_user.last_login = timezone.now()
    new_user.date_joined = new_user.last_login

    new_user.save()
    pending_user.delete()

    if admin_activation:
        msg = 'Accounts registration confirmed by ADMIN for %s' % new_user.username
    else:
        msg = 'Accounts registration confirmed by USER for %s from %s' % (
                new_user.username, ip)

    logger.info(msg)


def _absolute_url(url):
    site = Site.objects.get_current()
    return '%s://%s%s' % (settings.SITE_SCHEME, site.domain, url)


def send_email_change_confirmation(change):
    """Mail the confirmation link for a pending address change to its new address.

    Sent when a change is first requested and again on a resend, which is why
    it is separate from the courtesy note below: a resend is the same request
    again, and re-notifying the old address about it would be noise.

    """
    site = Site.objects.get_current()
    admin_email = settings.DEFAULT_FROM_EMAIL
    confirmation_link = _absolute_url(reverse('accounts-email_change_confirm',
            kwargs={'username': change.user.username, 'key': change.key}))

    msg = render_to_string('accounts/email_change_email.txt', {
        'site_name': site.name,
        'site_domain': site.domain,
        'username': change.user.username,
        'new_email': change.new_email,
        'confirmation_link': confirmation_link,
        'admin_email': admin_email,
        })

    send_mail('Confirm your new email address for ' + site.name, msg,
              admin_email, [change.new_email],
              category=EmailCategory.EMAIL_CHANGE)


def send_email_change_notice(change):
    """Tell the address on file that a change to it was requested.

    Carries no action link. There is no account-takeover path here -- login is
    by username, and a password reset mails its link to the address on file --
    so a "this wasn't me" link would add attack surface to answer a risk that
    does not exist. It names the contact form instead.

    """
    if not change.user.email:
        return

    site = Site.objects.get_current()
    admin_email = settings.DEFAULT_FROM_EMAIL

    msg = render_to_string('accounts/email_change_notice.txt', {
        'site_name': site.name,
        'site_domain': site.domain,
        'username': change.user.username,
        'new_email': change.new_email,
        'contact_link': _absolute_url(reverse('contact-form')),
        'admin_email': admin_email,
        })

    send_mail('Email address change requested for ' + site.name, msg,
              admin_email, [change.user.email],
              category=EmailCategory.EMAIL_CHANGE)
