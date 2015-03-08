"""
Views for the accounts application.

"""
import json
import logging

from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.conf import settings

from accounts.models import PendingUser
from accounts.forms import RegisterForm
from accounts.forms import RegisterCodeForm
from accounts.forms import ForgotUsernameForm
from accounts import create_new_user
from antispam.decorators import log_auth_failures


logger = logging.getLogger('auth')

#######################################################################

@log_auth_failures('Register')
def register(request):
    if request.user.is_authenticated():
        return redirect(settings.LOGIN_REDIRECT_URL)

    if request.method == 'POST':
        form = RegisterForm(request.POST, ip=request.META.get('REMOTE_ADDR', '?'))
        if form.is_valid():
            form.save(request)
            return redirect('accounts-register1')
    else:
        form = RegisterForm()

    return render(request, 'accounts/register.html', {'form': form})

#######################################################################

def register1(request):
    """Displays the registration code."""
    if request.user.is_authenticated():
        return redirect(settings.LOGIN_REDIRECT_URL)

    return render(request, 'accounts/register1.html')

#######################################################################

@log_auth_failures('Register')
def register2(request):
    """Processes the registration code and creates the user."""
    if request.user.is_authenticated():
        return redirect(settings.LOGIN_REDIRECT_URL)

    if request.method == 'POST':
        form = RegisterCodeForm(request.POST,
                                session=request.session,
                                ip=request.META.get('REMOTE_ADDR', '?'))
        if form.is_valid():
            form.save()
            return redirect('accounts-register_thanks')
    else:
        form = RegisterCodeForm()

    return render(request, 'accounts/register2.html', {'form': form})

#######################################################################

def get_code(request):
    code = {'code': 'FAIL-123'}
    reg_info = request.session.get('reg_info')
    if reg_info:
        code['code'] = reg_info.get('code', code['code'])

    return HttpResponse(json.dumps(code), content_type='application/json')

#######################################################################

def register_thanks(request):
    if request.user.is_authenticated():
        return redirect(settings.LOGIN_REDIRECT_URL)

    return render(request, 'accounts/register_thanks.html')

#######################################################################

def register_confirm(request, username, key):
    if request.user.is_authenticated():
        return redirect(settings.LOGIN_REDIRECT_URL)

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
        return redirect(settings.LOGIN_REDIRECT_URL)

    if request.method == 'POST':
        form = ForgotUsernameForm(data=request.POST)
        if form.is_valid():
            form.save()
            return redirect('accounts-username_sent')
    else:
        form = ForgotUsernameForm()

    return render(request, 'accounts/username_query.html', {'form': form})
