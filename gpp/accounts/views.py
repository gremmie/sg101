"""views for the accounts application"""

import datetime
import logging

from django.shortcuts import render_to_response
from django.template import RequestContext
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.conf import settings

from accounts.models import PendingUser
from accounts.forms import RegisterForm
from accounts import create_new_user


#######################################################################

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

    return render_to_response('accounts/register.html', {
                'form': form,
            },
            context_instance = RequestContext(request))

#######################################################################

def register_thanks(request):
    if request.user.is_authenticated():
        return HttpResponseRedirect(settings.LOGIN_REDIRECT_URL)

    return render_to_response('accounts/register_thanks.html',
            context_instance = RequestContext(request))

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
        return render_to_response('accounts/register_failure.html', {
            'username': username,
            },
            context_instance = RequestContext(request))

    if pending_user.key != key:
        logging.error('Accounts register_confirm [%s]: key error: %s', ip, username)
        return render_to_response('accounts/register_failure.html', {
            'username': username,
            },
            context_instance = RequestContext(request))

    create_new_user(pending_user, ip)

    return render_to_response('accounts/register_success.html', {
        'username': username,
        },
        context_instance = RequestContext(request))
