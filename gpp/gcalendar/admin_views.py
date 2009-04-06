"""
Admin views for the gcalendar application.
"""
from django.shortcuts import render_to_response
from django.template import RequestContext

from gcalendar.models import Event
from gcalendar.forms import PasswordForm
from gcalendar.calendar import Calendar
from gcalendar.calendar import CalendarError
import gcalendar.settings


def google_sync(request):
    """View to synchronize approved event changes with Google calendar."""
    events = Event.pending_events.all()
    messages = []
    errors = []
    if request.method == 'POST':
        form = PasswordForm(request.POST)
        if form.is_valid():
            try:
                cal = Calendar(gcalendar.settings.EMAIL,
                        form.cleaned_data['password'],
                        gcalendar.settings.CALENDAR_ID)
                cal.sync_events(events)
            except CalendarError, e:
                errors = e.errs
                events = Event.pending_events.all()
                form = PasswordForm()
            else:
                messages.append('All events processed successfully.')
                events = Event.objects.none()
                form = PasswordForm()

    else:
        form = PasswordForm()

    return render_to_response('gcalendar/google_sync.html', {
        'messages': messages,
        'errors': errors,
        'events': events,
        'form': form,
        },
        context_instance=RequestContext(request))

# vim: ts=4 sw=4
