"""
Views for the gcalendar application.
"""

from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.http import HttpResponseBadRequest
from django.http import HttpResponseForbidden
from django.http import HttpResponseRedirect
from django.http import Http404
from django.shortcuts import render_to_response
from django.shortcuts import get_object_or_404
from django.template import RequestContext

from gcalendar.forms import EventEntryForm
from gcalendar.models import Event


def index(request):
    return render_to_response('gcalendar/index.html', {
        },
        context_instance = RequestContext(request))


@login_required
def add_event(request):
    if request.method == 'POST':
        form = EventEntryForm(request.POST)
        if form.is_valid():
            event = form.save(commit=False)
            event.user = request.user
            event.repeat = 'none'
            event.save()
            return HttpResponseRedirect(reverse('gcalendar-add_thanks'))
    else:
        form = EventEntryForm()

    return render_to_response('gcalendar/event.html', {
        'title': 'Add Calendar Event',
        'form': form,
        },
        context_instance = RequestContext(request))


@login_required
def add_thanks(request):
    return render_to_response('gcalendar/thanks_add.html', {
        },
        context_instance = RequestContext(request))


@login_required
def edit_events(request):
    events = Event.objects.filter(user=request.user, status=Event.ON_CAL).order_by('start_date')
    return render_to_response('gcalendar/edit.html', {
        'events': events,
        },
        context_instance = RequestContext(request))


@login_required
def edit_event(request, event_id):
    event = get_object_or_404(Event, pk=event_id)
    if event.user != request.user:
        raise Http404

    if request.method == 'POST':
        form = EventEntryForm(request.POST, instance=event)
        if form.is_valid():
            event = form.save(commit=False)
            event.user = request.user
            event.repeat = 'none'
            event.status = Event.EDIT_REQ
            event.save()
            return HttpResponseRedirect(reverse('gcalendar-edit_thanks'))
    else:
        form = EventEntryForm(instance=event)

    return render_to_response('gcalendar/event.html', {
        'title': 'Change Calendar Event',
        'form': form,
        },
        context_instance = RequestContext(request))


@login_required
def edit_thanks(request):
    return render_to_response('gcalendar/thanks_edit.html', {
        },
        context_instance = RequestContext(request))


def delete_event(request):
    """This view marks an event for deletion. It is called via AJAX."""
    if request.user.is_authenticated():
        id = request.POST.get('id', None)
        if id is None or not id.isdigit():
            return HttpResponseBadRequest()
        try:
            event = Event.objects.get(pk=id)
        except Event.DoesNotExist:
            return HttpResponseBadRequest()
        if request.user != event.user:
            return HttpResponseForbidden()

        event.status = Event.DEL_REQ
        event.save()
        return HttpResponse(id)

    return HttpResponseForbidden()


# vim: ts=4 sw=4
