"""
This file contains the calendar class wich abstracts the Google gdata API for working with
Google Calendars.

"""
import datetime
import pytz

from django.utils.tzinfo import FixedOffset
from gdata.calendar.client import CalendarClient
from gdata.calendar.data import (CalendarEventEntry, CalendarEventFeed,
        CalendarWhere, When, EventWho)
import atom.data

from gcalendar.models import Event


class CalendarError(Exception):
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return repr(self.msg)


class Calendar(object):
    DATE_FMT = '%Y-%m-%d'
    DATE_TIME_FMT = DATE_FMT + 'T%H:%M:%S'
    DATE_TIME_TZ_FMT = DATE_TIME_FMT + '.000Z'

    def __init__(self, source=None, calendar_id='default', access_token=None):
        self.client = CalendarClient(source=source, auth_token=access_token)

        self.insert_feed = ('https://www.google.com/calendar/feeds/'
            '%s/private/full' % calendar_id)
        self.batch_feed = '%s/batch' % self.insert_feed

    def sync_events(self, qs):
        request_feed = CalendarEventFeed()
        for model in qs:
            if model.status == Event.NEW_APRV:
                event = CalendarEventEntry()
                request_feed.AddInsert(entry=self._populate_event(model, event))
            elif model.status == Event.EDIT_APRV:
                event = self._retrieve_event(model)
                request_feed.AddUpdate(entry=self._populate_event(model, event))
            elif model.status == Event.DEL_APRV:
                event = self._retrieve_event(model)
                request_feed.AddDelete(entry=event)
            else:
                assert False, 'unexpected status in sync_events'

        try:
            response_feed = self.client.ExecuteBatch(request_feed, self.batch_feed)
        except Exception, e:
            raise CalendarError('ExecuteBatch exception: %s' % e)

        err_msgs = []
        for entry in response_feed.entry:
            i = int(entry.batch_id.text)
            code = int(entry.batch_status.code)

            error = False
            if qs[i].status == Event.NEW_APRV:
                if code == 201:
                    qs[i].status = Event.ON_CAL
                    qs[i].google_id = entry.GetEditLink().href
                    qs[i].google_url = entry.GetHtmlLink().href
                    qs[i].save()
                    qs[i].notify_on_calendar()
                else:
                    error = True

            elif qs[i].status == Event.EDIT_APRV:
                if code == 200:
                    qs[i].status = Event.ON_CAL
                    qs[i].save()
                else:
                    error = True

            elif qs[i].status == Event.DEL_APRV:
                if code == 200:
                    qs[i].delete()
                else:
                    error = True

            if error:
                err_msgs.append('%s - (%d) %s' % (
                    qs[i].what, code, entry.batch_status.reason))

        if len(err_msgs) > 0:
            raise CalendarError(', '.join(err_msgs))

    def _retrieve_event(self, model):
        try:
            event = self.client.GetEventEntry(model.google_id)
        except Exception, e:
            raise CalendarError('Could not retrieve event from Google: %s, %s' \
                    % (model.what, e))
        return event

    def _populate_event(self, model, event):
        """Populates a gdata event from an Event model object."""
        event.title = atom.data.Title(text=model.what)
        event.content = atom.data.Content(text=model.html)
        event.where = [CalendarWhere(value=model.where)]
        event.who = [EventWho(email=model.user.email)]

        if model.all_day:
            start_time = self._make_time(model.start_date)
            if model.start_date == model.end_date:
                end_time = None
            else:
                end_time = self._make_time(model.end_date)
        else:
            start_time = self._make_time(model.start_date, model.start_time, model.time_zone)
            end_time = self._make_time(model.end_date, model.end_time, model.time_zone)

        event.when = [When(start=start_time, end=end_time)]
        return event

    def _make_time(self, date, time=None, tz_name=None):
        """
        Returns the gdata formatted date/time string given a date, optional time,
        and optional time zone name (e.g. 'US/Pacific'). If the time zone name is None,
        no time zone info will be added to the string.
        """

        if time is not None:
            d = datetime.datetime.combine(date, time)
        else:
            d = datetime.datetime(date.year, date.month, date.day)

        if time is None:
            s = d.strftime(self.DATE_FMT)
        elif tz_name is None:
            s = d.strftime(self.DATE_TIME_FMT)
        else:
            try:
                tz = pytz.timezone(tz_name)
            except pytz.UnknownTimeZoneError:
                raise CalendarError('Invalid time zone: %s' (tz_name,))
            local = tz.localize(d)
            zulu = local.astimezone(FixedOffset(0))
            s = zulu.strftime(self.DATE_TIME_TZ_FMT)

        return s

