"""
Views for the accounts application.

"""
import datetime
import json
import logging

from django.shortcuts import render
from django.template import RequestContext
from django.template.loader import render_to_string
from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.conf import settings
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login

from accounts.models import PendingUser
from accounts.forms import RegisterForm, ForgotUsernameForm
from accounts import create_new_user
from antispam.decorators import rate_limit


#######################################################################

@rate_limit(count=10, interval=datetime.timedelta(minutes=1))
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
        logging.error('Accounts register_confirm [%s]: user does not exist: %s', ip, username)
        return render(request,
                  'accounts/register_failure.html',
                  {'username': username})

    if pending_user.key != key:
        logging.error('Accounts register_confirm [%s]: key error: %s', ip, username)
        return render(request,
                'accounts/register_failure.html',
                {'username': username})

    create_new_user(pending_user, ip)

    return render(request,
            'accounts/register_success.html',
            {'username': username})

#######################################################################

@rate_limit(count=10, interval=datetime.timedelta(minutes=1),
        lockout=datetime.timedelta(minutes=2))
def login_ajax(request):
    """
    This view function handles a login via AJAX.

    """
    if not request.is_ajax():
        return HttpResponseRedirect(reverse('accounts-login'))

    response = {
        'success': False,
        'error': '',
        'navbar_html': ''
    }

    if request.method == "POST":
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            response['success'] = True
            response['navbar_html'] = render_to_string('navbar.html',
                    {'user': request.user}, RequestContext(request))
        else:
            response['error'] = 'Invalid username or password'

    return HttpResponse(json.dumps(response), content_type='application/json')

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
