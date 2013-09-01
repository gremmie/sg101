"""
Views for the accounts application.

"""
import logging

from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.conf import settings

from accounts.models import PendingUser
from accounts.forms import RegisterForm, ForgotUsernameForm
from accounts import create_new_user
from antispam.decorators import log_auth_failures


logger = logging.getLogger('auth')

#######################################################################

@log_auth_failures('Register')
def register(request):
    if request.user.is_authenticated():
        return HttpResponseRedirect(settings.LOGIN_REDIRECT_URL)

    if request.method == 'POST':
        form = RegisterForm(request.POST, ip=request.META.get('REMOTE_ADDR', '?'))
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('accounts.views.register_thanks'))
    else:
        form = RegisterForm()

    return render(request, 'accounts/register.html', {'form': form})

#######################################################################

def register_thanks(request):
    if request.user.is_authenticated():
        return HttpResponseRedirect(settings.LOGIN_REDIRECT_URL)

    return render(request, 'accounts/register_thanks.html')

#######################################################################

def register_confirm(request, username, key):
    if request.user.is_authenticated():
        return HttpResponseRedirect(settings.LOGIN_REDIRECT_URL)

    # purge expired users

    PendingUser.objects.purge_expired()

    ip = request.META.get('REMOTE_ADDR', '?')
    try:
        pending_user = PendingUser.objects.get(username = username)
    except PendingUser.DoesNotExist:
        logger.error('Accounts register_confirm [%s]: user does not exist: %s', ip, username)
        return render(request,
                  'accounts/register_failure.html',
                  {'username': username})

    if pending_user.key != key:
        logger.error('Accounts register_confirm [%s]: key error: %s', ip, username)
        return render(request,
                'accounts/register_failure.html',
                {'username': username})

    create_new_user(pending_user, ip)

    return render(request,
            'accounts/register_success.html',
            {'username': username})

#######################################################################

def username_query(request):
    """This view handles forgotten username queries."""
    if request.user.is_authenticated():
        return HttpResponseRedirect(settings.LOGIN_REDIRECT_URL)

    if request.method == 'POST':
        form = ForgotUsernameForm(data=request.POST)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('accounts-username_sent'))
    else:
        form = ForgotUsernameForm()

    return render(request, 'accounts/username_query.html', {'form': form})
