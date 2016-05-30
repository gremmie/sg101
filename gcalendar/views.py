"""
Views for the gcalendar application.
"""

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import InvalidPage
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.http import HttpResponseBadRequest
from django.http import HttpResponseForbidden
from django.http import HttpResponseRedirect
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.shortcuts import render

from core.functions import get_page
from core.paginator import DiggPaginator
from gcalendar.forms import EventEntryForm
from gcalendar.models import Event


def index(request):
    user = request.user
    if user.is_authenticated():
        tz = user.profile.time_zone
    else:
        tz = 'US/Pacific'

    return render(request, 'gcalendar/index.html', {
        'tz': tz,
        'V3_DESIGN': True,
        })


@login_required
def add_event(request):
    if request.method == 'POST':
        form = EventEntryForm(request.POST)
        if form.is_valid():
            event = form.save(commit=False)
            event.user = request.user
            event.repeat = 'none'
            event.save(html=form.html)
            return HttpResponseRedirect(reverse('gcalendar-add_thanks'))
    else:
        form = EventEntryForm()

    return render(request, 'gcalendar/event.html', {
        'title': 'Add Calendar Event',
        'form': form,
        'V3_DESIGN': True,
        })


@login_required
def add_thanks(request):
    return render(request, 'gcalendar/thanks_add.html', {
        })


@login_required
def edit_events(request):
    events = Event.objects.filter(user=request.user, status=Event.ON_CAL).\
            order_by('-start_date')
    paginator = DiggPaginator(events, 25, body=5, tail=2, margin=3, padding=2)
    num = get_page(request.GET)
    try:
        page = paginator.page(num)
    except InvalidPage:
        raise Http404

    return render(request, 'gcalendar/edit.html', {
        'page': page,
        'V3_DESIGN': True,
        })


@login_required
def edit_event(request, event_id):
    event = get_object_or_404(Event, pk=event_id)
    if event.user != request.user:
        raise PermissionDenied

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

    return render(request, 'gcalendar/event.html', {
        'title': 'Change Calendar Event',
        'form': form,
        })


@login_required
def edit_thanks(request):
    return render(request, 'gcalendar/thanks_edit.html', {
        })


def delete_event(request):
    """This view marks an event for deletion. It is called via AJAX."""
    if request.user.is_authenticated():
        event_id = request.POST.get('id')
        if event_id is None or not event_id.isdigit():
            return HttpResponseBadRequest()
        try:
            event = Event.objects.get(pk=event_id)
        except Event.DoesNotExist:
            return HttpResponseBadRequest()
        if request.user != event.user:
            return HttpResponseForbidden()

        event.status = Event.DEL_REQ
        event.save()
        return HttpResponse(event_id, content_type="text/plain")

    return HttpResponseForbidden()
