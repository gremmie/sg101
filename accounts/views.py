"""
Views for the accounts application.

"""
import logging
import secrets

from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.conf import settings
from django.views.generic import TemplateView

from accounts.models import PendingEmailChange
from accounts.models import PendingUser
from accounts.forms import RegisterForm
from accounts.forms import ForgotUsernameForm
from accounts.utils import create_new_user
from antispam.decorators import log_auth_failures


logger = logging.getLogger('auth')

#######################################################################

@log_auth_failures('Register')
def register(request):
    if request.user.is_authenticated:
        return redirect(settings.LOGIN_REDIRECT_URL)

    if request.method == 'POST':
        form = RegisterForm(request.POST,
                            ip=request.META.get('REMOTE_ADDR', '?'),
                            token=request.POST.get('cf-turnstile-response'))
        if form.is_valid():
            form.save()
            return redirect('accounts-register_thanks')
    else:
        form = RegisterForm()

    return render(request, 'accounts/register.html', {
        'form': form,
        'TURNSTILE_SITE_KEY': settings.TURNSTILE_SITE_KEY,
        'V3_DESIGN': True,
    })

#######################################################################

def register_thanks(request):
    if request.user.is_authenticated:
        return redirect(settings.LOGIN_REDIRECT_URL)

    return render(request, 'accounts/register_thanks.html', {
        'V3_DESIGN': True,
    })

#######################################################################

def register_confirm(request, username, key):
    if request.user.is_authenticated:
        return redirect(settings.LOGIN_REDIRECT_URL)

    # purge expired users

    PendingUser.objects.purge_expired()

    ip = request.META.get('REMOTE_ADDR', '?')
    try:
        pending_user = PendingUser.objects.get(username__iexact=username)
    except PendingUser.DoesNotExist:
        logger.error('Accounts register_confirm [%s]: user does not exist: %s',
                     ip, username)
        return render(request, 'accounts/register_failure.html', {
            'username': username,
            'V3_DESIGN': True,
        })

    if not secrets.compare_digest(pending_user.key, key):
        logger.error('Accounts register_confirm [%s]: key error: %s', ip, username)
        return render(request, 'accounts/register_failure.html', {
            'username': username,
            'V3_DESIGN': True,
        })

    create_new_user(pending_user, ip)

    return render(request, 'accounts/register_success.html', {
        'username': username,
        'V3_DESIGN': True,
    })

#######################################################################

def _email_change_failure(request, reason):
    return render(request, 'accounts/email_change_failure.html', {
        'reason': reason,
        'V3_DESIGN': True,
    })


def email_change_confirm(request, username, key):
    """Apply a pending email address change, if the key is good.

    Deliberately not login_required: the link is read in the new mailbox, which
    may be on another device entirely. Possession of the key is the proof, so
    the row is found by username and the key is then compared -- rather than
    looked up, which would make the key a database index instead of a secret.

    """
    ip = request.META.get('REMOTE_ADDR', '?')
    try:
        change = PendingEmailChange.objects.get(user__username__iexact=username)
    except PendingEmailChange.DoesNotExist:
        logger.error('Accounts email_change_confirm [%s]: no request for %s',
                     ip, username)
        return _email_change_failure(request, 'unknown')

    # Checked before the key so an expired link can say so. Purging first --
    # the way register_confirm does -- would leave an expired link
    # indistinguishable from a mistyped one.
    if change.is_expired:
        change.delete()
        logger.info('Accounts email_change_confirm [%s]: expired for %s',
                    ip, username)
        return _email_change_failure(request, 'expired')

    if not secrets.compare_digest(change.key, key):
        logger.error('Accounts email_change_confirm [%s]: key error: %s',
                     ip, username)
        return _email_change_failure(request, 'unknown')

    user = change.user
    # Nobody held the address when the change was requested, but two members
    # can request the same free address and both confirm. Without this the
    # flow mints the sort of duplicate pair it exists to prevent.
    if User.objects.filter(email__iexact=change.new_email).exclude(
            pk=user.pk).exists():
        logger.error('Accounts email_change_confirm [%s]: %s is taken, for %s',
                     ip, change.new_email, username)
        return _email_change_failure(request, 'taken')

    user.email = change.new_email
    user.save()
    change.delete()
    logger.info('Accounts email change confirmed for %s from %s', username, ip)

    return render(request, 'accounts/email_change_success.html', {
        'new_email': user.email,
        'V3_DESIGN': True,
    })

#######################################################################

def username_query(request):
    """This view handles forgotten username queries."""
    if request.user.is_authenticated:
        return redirect(settings.LOGIN_REDIRECT_URL)

    if request.method == 'POST':
        form = ForgotUsernameForm(data=request.POST)
        if form.is_valid():
            form.save()
            return redirect('accounts-username_sent')
    else:
        form = ForgotUsernameForm()

    return render(request, 'accounts/username_query.html', {
        'form': form,
        'V3_DESIGN': True,
    })


class UsernameSentView(TemplateView):
    template_name = 'accounts/username_sent.html'

    def get_context_data(self, **kwargs):
        context = super(UsernameSentView, self).get_context_data(**kwargs)
        context['V3_DESIGN'] = True
        return context
