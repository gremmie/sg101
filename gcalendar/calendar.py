"""
This file contains the calendar class wich abstracts the Google API for working
with Google Calendars.

"""
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
import datetime

# Temporarily disabled at the Python 3 flip: the Google API client stack
# (httplib2 / apiclient / oauth2client) pinned here is Py2-era and dropped from
# the requirements. gcalendar is slated for revival with the modern google-auth
# libraries in a later step. Until then this module still imports (so the admin
# imports cleanly), but constructing a Calendar raises.
try:
    import httplib2
    from apiclient.discovery import build
    from apiclient.http import BatchHttpRequest
    _GCAL_API_AVAILABLE = True
except ImportError:  # Google API client not installed on Python 3 yet
    httplib2 = None
    build = None
    BatchHttpRequest = None
    _GCAL_API_AVAILABLE = False

from django.utils.timezone import get_fixed_timezone

from gcalendar.models import Event


class CalendarError(Exception):
    """Calendar exception base class."""


def _make_err_msg(event, exception):
    """Returns an error message string from the given Event and exception."""
    return '%s - %s' % (event.what, exception)


class Calendar(object):
    DATE_TIME_FMT = '%Y-%m-%dT%H:%M:%S'
    DATE_TIME_TZ_FMT = DATE_TIME_FMT + 'Z'

    def __init__(self, calendar_id='primary', credentials=None):
        if not _GCAL_API_AVAILABLE:
            raise NotImplementedError(
                "Google Calendar sync is temporarily disabled: the Google API "
                "client stack is not available on Python 3 yet. It will be "
                "revived with the modern google-auth libraries.")
        self.calendar_id = calendar_id
        http = httplib2.Http()
        if credentials:
            http = credentials.authorize(http)
        self.service = build('calendar', 'v3', http=http)

    def sync_events(self, qs):
        """Process the pending events in a batch request to the Google calendar
        API.
        """
        batch = BatchHttpRequest()

        err_msgs = []
        def insert_callback(request_id, event, exception):
            n = int(request_id)
            if not exception:
                qs[n].status = Event.ON_CAL
                qs[n].google_id = event['id']
                qs[n].google_url = event['htmlLink']
                qs[n].save()
                qs[n].notify_on_calendar()
            else:
                err_msgs.append(_make_err_msg(qs[n], exception))

        def update_callback(request_id, event, exception):
            n = int(request_id)
            if not exception:
                qs[n].status = Event.ON_CAL
                qs[n].save()
            else:
                err_msgs.append(_make_err_msg(qs[n], exception))

        def delete_callback(request_id, response, exception):
            n = int(request_id)
            if not exception:
                qs[n].delete()
            else:
                err_msgs.append(_make_err_msg(qs[n], exception))

        for n, event in enumerate(qs):
            if event.status == Event.NEW_APRV:
                batch.add(self.service.events().insert(calendarId=self.calendar_id,
                            body=self._make_event(event)),
                        callback=insert_callback,
                        request_id=str(n))
            elif event.status == Event.EDIT_APRV:
                batch.add(self.service.events().update(calendarId=self.calendar_id,
                            eventId=event.google_id,
                            body=self._make_event(event)),
                        callback=update_callback,
                        request_id=str(n))
            elif event.status == Event.DEL_APRV:
                batch.add(self.service.events().delete(calendarId=self.calendar_id,
                            eventId=event.google_id),
                        callback=delete_callback,
                        request_id=str(n))
            else:
                raise CalendarError("Invalid event status: %s" % event.status)

        try:
            batch.execute()
        except Exception as ex:
            raise CalendarError('Batch exception: %s' % ex)

        if err_msgs:
            raise CalendarError(', '.join(err_msgs))

    def _make_event(self, model):
        """Creates an event body from a model instance."""
        event = {
            'summary': model.what,
            'description': model.html,
            'location': model.where,
            'anyoneCanAddSelf': True,
        }

        if model.all_day:
            start = {'date': model.start_date.isoformat()}
            end = {'date': model.end_date.isoformat()}
        else:
            start = {'dateTime': self._make_time(model.start_date, model.start_time,
                                                 model.time_zone)}
            end = {'dateTime': self._make_time(model.end_date, model.end_time,
                                               model.time_zone)}

        event['start'] = start
        event['end'] = end
        return event

    def _make_time(self, date, time=None, tz_name=None):
        """
        Returns the formatted date/time string given a date, optional time, and
        optional time zone name (e.g. 'US/Pacific'). If the time zone name is
        None, no time zone info will be added to the string.
        """

        if time:
            d = datetime.datetime.combine(date, time)
        else:
            d = datetime.datetime(date.year, date.month, date.day)

        if not tz_name:
            s = d.strftime(self.DATE_TIME_FMT)
        else:
            try:
                tz = ZoneInfo(tz_name)
            except (ZoneInfoNotFoundError, ValueError):
                # ValueError covers empty and path-shaped input; see the same
                # validator in bio/forms.py.
                raise CalendarError('Invalid time zone: %s' % tz_name)
            local = d.replace(tzinfo=tz)
            zulu = local.astimezone(get_fixed_timezone(0))
            s = zulu.strftime(self.DATE_TIME_TZ_FMT)

        return s
