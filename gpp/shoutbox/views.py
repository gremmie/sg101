"""
Views for the Shoutbox application.
"""

import re
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.core.paginator import InvalidPage
from django.http import HttpResponse
from django.http import HttpResponseBadRequest
from django.http import HttpResponseForbidden
from django.http import HttpResponseRedirect
from django.http import Http404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST

from core.paginator import DiggPaginator
from core.functions import email_admins
from shoutbox.forms import ShoutBoxForm
from shoutbox.models import Shout
from shoutbox.models import ShoutFlag

SHOUTS_PER_PAGE = 10

@login_required
@require_POST
def shout(request):
    msg = request.POST.get('msg', '').strip()
    if msg == '':
        return HttpResponse('')

    shout = Shout(user=request.user, shout=msg)
    shout.save()
    return render_to_response('shoutbox/shout.html', {
       'shout': shout,
       },
       context_instance = RequestContext(request))


def view_shout(request, id):
    """This view is for viewing an individual shout."""
    try:
        shout = Shout.objects.get(pk=id)
    except Shout.DoesNotExist:
        return render_to_response('shoutbox/missing_shout.html', {},
           context_instance = RequestContext(request))

    return render_to_response('shoutbox/view_shout.html', {
       'shout': shout,
       },
       context_instance = RequestContext(request))


def view_history(request, page=1):
    """This view allows one to view the shoutbox history."""
    paginator = DiggPaginator(Shout.objects.all().select_related(), 
            SHOUTS_PER_PAGE, body=5, tail=3, margin=3, padding=2)
    try:
        the_page = paginator.page(int(page))
    except InvalidPage:
        raise Http404

    return render_to_response('shoutbox/view.html', {
        'page': the_page,
        },
        context_instance = RequestContext(request))
   

shout_id_re = re.compile(r'shout-(\d+)')

def text(request):
    """This view function retrieves the text of a shout; it is used in the in-place
    editing of shouts on the shoutbox history view."""
    if request.user.is_authenticated():
        m = shout_id_re.match(request.GET.get('id', ''))
        if m is None:
            return HttpResponseBadRequest()
        try:
            shout = Shout.objects.get(pk=m.group(1))
        except Shout.DoesNotExist:
            return HttpResponseBadRequest()
        return HttpResponse(shout.shout)

    return HttpResponseForbidden()


def edit(request):
    """This view accepts a shoutbox edit from the shoutbox history view."""
    if request.user.is_authenticated():
        m = shout_id_re.match(request.POST.get('id', ''))
        if m is None:
            return HttpResponseBadRequest()
        try:
            shout = Shout.objects.get(pk=m.group(1))
        except Shout.DoesNotExist:
            return HttpResponseBadRequest()
        if request.user != shout.user:
            return HttpResponseForbidden()
        new_shout = request.POST.get('value', '').strip()
        if new_shout == '':
            return HttpResponseBadRequest()
        shout.shout = new_shout
        shout.save()
        return HttpResponse(shout.html)

    return HttpResponseForbidden()


def delete(request):
    """This view deletes a shout. It is called by AJAX from the shoutbox history view."""
    if request.user.is_authenticated():
        id = request.POST.get('id', None)
        if id is None or not id.isdigit():
            return HttpResponseBadRequest()
        try:
            shout = Shout.objects.get(pk=id)
        except Shout.DoesNotExist:
            return HttpResponseBadRequest()
        if request.user != shout.user:
            return HttpResponseForbidden()
        shout.delete()
        return HttpResponse(id)

    return HttpResponseForbidden()


@require_POST
def flag(request):
    """
    This function handles the flagging of shouts by users. This function should
    be the target of an AJAX post.
    """
    if not request.user.is_authenticated():
        return HttpResponse('Please login or register to flag a shout.')

    id = request.POST.get('id', None)
    if id is None:
        return HttpResponseBadRequest('No id')

    try:
        shout = Shout.objects.get(pk=id)
    except Shout.DoesNotExist:
        return HttpResponseBadRequest('No shout with id %s' % id)

    flag = ShoutFlag(user=request.user, shout=shout)
    flag.save()
    email_admins('A Shout Has Been Flagged', """Hello,

A user has flagged a shout for review.
""")
    return HttpResponse('The shout was flagged. A moderator will review the shout shortly. ' \
            'Thanks for helping to improve the quality of this site.')

# vim: ts=4 sw=4
