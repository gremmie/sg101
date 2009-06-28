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
    err_msg = ''
    if request.method == 'POST':
        form = PasswordForm(request.POST)
        if form.is_valid():
            try:
                cal = Calendar(gcalendar.settings.EMAIL,
                        form.cleaned_data['password'],
                        gcalendar.settings.CALENDAR_ID)
                cal.sync_events(events)
            except CalendarError, e:
                err_msg = e.msg
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
        'err_msg': err_msg,
        'events': events,
        'form': form,
        },
        context_instance=RequestContext(request))

