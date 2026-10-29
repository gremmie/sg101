"""
Views for the gcalendar application.
"""
from urllib.parse import urlencode

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import InvalidPage
from django.urls import reverse
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


# The calendars shown on the calendar page, in order. The name is only for
# whoever edits this list; the embed shows each calendar's own Google title.
EMBEDDED_CALENDARS = [
    ('SurfGuitar101', settings.GCAL_CALENDAR_ID, '#1B887A'),
    ('Various Surf Radio Shows',
     'qrihvvsqabp3i3uv8gj4i5lfik@group.calendar.google.com', '#AB8B00'),
    ('The Electric Heaters',
     '59p0500pnuvles8a0j71prauqg@group.calendar.google.com', '#2952A3'),
]


def _embed_url(tz):
    """Return the Google Calendar embed URL showing EMBEDDED_CALENDARS in the
    time zone tz.

    """
    params = [('showTitle', 0), ('mode', 'AGENDA'), ('height', 640),
              ('wkst', 1), ('bgcolor', '#FFFFFF')]
    for _name, calendar_id, color in EMBEDDED_CALENDARS:
        params += [('src', calendar_id), ('color', color)]
    params.append(('ctz', tz))
    return 'https://www.google.com/calendar/embed?' + urlencode(params)


def index(request):
    user = request.user
    if user.is_authenticated:
        tz = user.profile.time_zone
    else:
        tz = 'US/Pacific'

    return render(request, 'gcalendar/index.html', {
        'tz': tz,
        'embed_url': _embed_url(tz),
        'V3_DESIGN': True,
        })


@login_required
def add_event(request):
    thanks_flag = False
    if request.method == 'POST':
        form = EventEntryForm(request.POST)
        if form.is_valid():
            event = form.save(commit=False)
            event.user = request.user
            event.save(html=form.html)
            return HttpResponseRedirect(reverse('gcalendar-add') + '?thanks=1')
    else:
        form = EventEntryForm()
        thanks_flag = bool(request.GET.get('thanks', False))

    return render(request, 'gcalendar/event.html', {
        'title': 'Add Calendar Event',
        'form': form,
        'is_new': True,
        'thanks_flag': thanks_flag,
        'V3_DESIGN': True,
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
        'thanks_flag': bool(request.GET.get('thanks', False)),
        'V3_DESIGN': True,
        })


@login_required
def edit_event(request, event_id):
    # Only an event actually on the calendar can be changed, which is the same
    # rule edit_events lists by. An event with a change already pending is
    # waiting on the staff, and its status is what puts it in the sync queue:
    # editing one out of a kept URL would take it back out again silently.
    event = get_object_or_404(Event, pk=event_id, status=Event.ON_CAL)
    if event.user != request.user:
        raise PermissionDenied

    if request.method == 'POST':
        form = EventEntryForm(request.POST, instance=event)
        if form.is_valid():
            event = form.save(commit=False)
            event.user = request.user
            event.status = Event.EDIT_REQ
            event.save()
            return HttpResponseRedirect(reverse('gcalendar-edit_events') + '?thanks=1')
    else:
        form = EventEntryForm(instance=event)

    return render(request, 'gcalendar/event.html', {
        'title': 'Change Calendar Event',
        'form': form,
        'is_new': False,
        'V3_DESIGN': True,
        })


def delete_event(request):
    """This view marks an event for deletion. It is called via AJAX."""
    if request.user.is_authenticated:
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
