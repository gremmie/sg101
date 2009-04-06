"""
Views for the Shoutbox application.
"""

import re
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponse
from django.http import HttpResponseBadRequest
from django.http import HttpResponseForbidden
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required

from core.paginator import DiggPaginator
from shoutbox.forms import ShoutBoxForm
from shoutbox.models import Shout

SHOUTS_PER_PAGE = 10

@login_required
def shout(request):
    if request.method == 'POST':
        msg = request.POST.get('msg', '').strip()
        if msg != '':
            shout = Shout(user=request.user, shout=msg)
            shout.save()
            
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))


def view(request, page=1):
    """This view allows one to view the shoutbox history."""
    paginator = DiggPaginator(Shout.objects.all(), SHOUTS_PER_PAGE, body=5, tail=3, margin=3, padding=2)
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
        return render_to_response('shoutbox/render_shout.html', {
            'shout': shout,
            },
            context_instance = RequestContext(request))

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
