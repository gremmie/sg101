"""Unit tests for the Calendar wrapper around the Google Calendar API.

Everything Google is mocked here, so these prove we call the API the way we
intend to -- not that the calls succeed against a real calendar. Two things in
particular are outside what any mock can answer, and both are checked by hand
against the live calendar: whether `anyoneCanAddSelf` is honored on an event a
service account inserts, and whether the service account may edit and delete
the events a human account created years ago.

The time zone conversions are the exception: those run for real, because the
UTC string they produce is what decides the hour an event shows up at.

"""
import datetime
import json
import os
import tempfile
import unittest

from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase

import gcalendar.calendar
from gcalendar.calendar import Calendar, CalendarError
from gcalendar.models import Event


class FakeBatch(object):
    """Stands in for the object service.new_batch_http_request() returns.

    It records what was added and, on execute(), hands each callback the
    (response, exception) pair the test scripted for that request id. The real
    batch calls back with what Google returned; this calls back with what the
    test says Google returned.

    """
    def __init__(self, responses=None, execute_error=None):
        self.responses = responses or {}
        self.execute_error = execute_error
        self.added = []

    def add(self, request, callback=None, request_id=None):
        self.added.append((request, callback, request_id))

    def execute(self):
        if self.execute_error:
            raise self.execute_error
        for request, callback, request_id in self.added:
            response, exception = self.responses.get(request_id, ({}, None))
            callback(request_id, response, exception)


class CredentialsTestCase(unittest.TestCase):
    """How a Calendar gets hold of the service account it acts as."""

    @patch('gcalendar.calendar.build')
    @patch('gcalendar.calendar.service_account')
    def test_service_is_built_from_the_service_account_key(self, mock_sa,
                                                           mock_build):
        cal = Calendar('cal-id', '/keys/sa.json')

        mock_sa.Credentials.from_service_account_file.assert_called_once_with(
            '/keys/sa.json', scopes=['https://www.googleapis.com/auth/calendar'])
        creds = mock_sa.Credentials.from_service_account_file.return_value
        mock_build.assert_called_once_with('calendar', 'v3', credentials=creds)
        self.assertIs(cal.service, mock_build.return_value)
        self.assertEqual(cal.calendar_id, 'cal-id')

        # The Python 3 flip left an import guard here that made constructing a
        # Calendar raise; the modern libraries are a real dependency now.
        self.assertFalse(hasattr(gcalendar.calendar, '_GCAL_API_AVAILABLE'))

    def test_a_missing_key_file_is_a_calendar_error(self):
        """Not an OSError: the sync view renders CalendarError into the page."""
        with self.assertRaises(CalendarError):
            Calendar('cal-id', '/no/such/service-account.json')

    def test_a_blank_credentials_path_says_so(self):
        """Blank is the default -- an install that never configured this. The
        message reaches the admin's sync page, so it has to say which setting
        is empty rather than report a stat of ''.

        """
        with self.assertRaises(CalendarError) as caught:
            Calendar('cal-id', '')

        self.assertIn('GCAL_CREDENTIALS_PATH', str(caught.exception))
        self.assertNotIn('No such file', str(caught.exception))

    def test_a_key_file_that_is_not_json_is_a_calendar_error(self):
        with self._key_file('this is not json') as path:
            with self.assertRaises(CalendarError):
                Calendar('cal-id', path)

    def test_json_that_is_not_a_service_account_key_is_a_calendar_error(self):
        """An authorized-user token file is the plausible wrong file to point at."""
        with self._key_file(json.dumps({'type': 'authorized_user'})) as path:
            with self.assertRaises(CalendarError):
                Calendar('cal-id', path)

    def _key_file(self, contents):
        """A temporary file holding contents, removed on exit."""
        class _Key(object):
            def __enter__(inner):
                fd, inner.path = tempfile.mkstemp(suffix='.json')
                os.write(fd, contents.encode())
                os.close(fd)
                return inner.path

            def __exit__(inner, *exc):
                os.remove(inner.path)
                return False

        return _Key()


class EventBodyTestCase(unittest.TestCase):
    """The event body handed to Google, and the times inside it."""

    def setUp(self):
        for target in ('gcalendar.calendar.service_account',
                       'gcalendar.calendar.build'):
            patcher = patch(target)
            patcher.start()
            self.addCleanup(patcher.stop)
        self.cal = Calendar('cal-id', 'sa.json')

    def test_local_time_becomes_utc_in_summer(self):
        s = self.cal._make_time(datetime.date(2026, 7, 4),
                                datetime.time(20, 30), 'US/Pacific')
        self.assertEqual(s, '2026-07-05T03:30:00Z')

    def test_local_time_becomes_utc_in_winter(self):
        """The pair with the summer test is the point.

        A single date cannot tell a real zone lookup from a hardcoded offset:
        July is UTC-7 in US/Pacific and January is UTC-8, so an implementation
        that ignored daylight saving would pass one of these and fail the other.

        """
        s = self.cal._make_time(datetime.date(2026, 1, 10),
                                datetime.time(20, 30), 'US/Pacific')
        self.assertEqual(s, '2026-01-11T04:30:00Z')

    def test_without_a_zone_the_time_is_left_naive(self):
        s = self.cal._make_time(datetime.date(2026, 7, 4),
                                datetime.time(20, 30))
        self.assertEqual(s, '2026-07-04T20:30:00')

    def test_a_blank_zone_is_not_an_error(self):
        """Event.time_zone is blank=True, so blank is the ordinary case."""
        s = self.cal._make_time(datetime.date(2026, 7, 4),
                                datetime.time(20, 30), '')
        self.assertEqual(s, '2026-07-04T20:30:00')

    def test_without_a_time_the_day_starts_at_midnight(self):
        self.assertEqual(self.cal._make_time(datetime.date(2026, 7, 4)),
                         '2026-07-04T00:00:00')
        self.assertEqual(
            self.cal._make_time(datetime.date(2026, 7, 4), None, 'US/Pacific'),
            '2026-07-04T07:00:00Z')

    def test_an_unusable_zone_name_is_a_calendar_error(self):
        for tz_name in ['Not/AZone', 'US/Pacific/extra', '../../etc/passwd']:
            with self.subTest(tz_name=tz_name):
                with self.assertRaises(CalendarError):
                    self.cal._make_time(datetime.date(2026, 7, 4),
                                        datetime.time(20, 30), tz_name)

    def test_a_timed_event_body_carries_datetimes(self):
        event = Event(what='Surf Show', description='Come on down',
                      html='<p>Come on down</p>', where='The Beach',
                      start_date=datetime.date(2026, 7, 4),
                      start_time=datetime.time(20, 0),
                      end_date=datetime.date(2026, 7, 4),
                      end_time=datetime.time(23, 0),
                      time_zone='US/Pacific')

        self.assertEqual(self.cal._make_event(event), {
            'summary': 'Surf Show',
            'description': '<p>Come on down</p>',
            'location': 'The Beach',
            'anyoneCanAddSelf': True,
            'start': {'dateTime': '2026-07-05T03:00:00Z'},
            'end': {'dateTime': '2026-07-05T06:00:00Z'},
        })

    def test_an_all_day_event_body_carries_plain_dates(self):
        event = Event(what='Surf Camp', description='All week',
                      html='<p>All week</p>', where='The Beach', all_day=True,
                      start_date=datetime.date(2026, 7, 4),
                      end_date=datetime.date(2026, 7, 11),
                      time_zone='US/Pacific')

        body = self.cal._make_event(event)
        self.assertEqual(body['start'], {'date': '2026-07-04'})
        self.assertEqual(body['end'], {'date': '2026-07-11'})
        self.assertTrue(body['anyoneCanAddSelf'])


class SyncEventsTestCase(TestCase):
    """The batch that pushes approved events onto the calendar.

    These write to the database, because writing back what Google returned --
    and deleting the row for an event removed from the calendar -- is the
    behavior under test.

    """
    def setUp(self):
        self.user = User.objects.create_user('brian', 'brian@example.com', 'pw')
        for target in ('gcalendar.calendar.service_account',
                       'gcalendar.calendar.build'):
            patcher = patch(target)
            patcher.start()
            self.addCleanup(patcher.stop)

    def _event(self, status, what='An Event', google_id=''):
        return Event.objects.create(user=self.user, what=what, status=status,
                                    where='The Beach',
                                    start_date=datetime.date(2026, 7, 4),
                                    end_date=datetime.date(2026, 7, 4),
                                    google_id=google_id, all_day=True)

    def _calendar(self, batch):
        cal = Calendar('cal-id', 'sa.json')
        cal.service.new_batch_http_request.return_value = batch
        return cal

    def test_an_approved_event_is_inserted_and_recorded(self):
        event = self._event(Event.NEW_APRV)
        batch = FakeBatch({'0': ({'id': 'goog-1',
                                  'htmlLink': 'https://cal/goog-1'}, None)})
        cal = self._calendar(batch)

        with patch.object(Event, 'notify_on_calendar') as notify:
            cal.sync_events(Event.pending_events.all())

        event.refresh_from_db()
        self.assertEqual(event.status, Event.ON_CAL)
        self.assertEqual(event.google_id, 'goog-1')
        self.assertEqual(event.google_url, 'https://cal/goog-1')
        notify.assert_called_once_with()

        cal.service.events.return_value.insert.assert_called_once()
        kwargs = cal.service.events.return_value.insert.call_args.kwargs
        self.assertEqual(kwargs['calendarId'], 'cal-id')
        self.assertEqual(kwargs['body']['summary'], 'An Event')

    def test_the_batch_is_built_from_the_service(self):
        """v2 binds a batch to the API's own endpoint; the global one is gone."""
        self._event(Event.NEW_APRV)
        batch = FakeBatch({'0': ({'id': 'g', 'htmlLink': 'u'}, None)})
        cal = self._calendar(batch)

        with patch.object(Event, 'notify_on_calendar'):
            cal.sync_events(Event.pending_events.all())

        cal.service.new_batch_http_request.assert_called_once_with()

    def test_an_approved_edit_is_updated(self):
        event = self._event(Event.EDIT_APRV, google_id='goog-7')
        cal = self._calendar(FakeBatch({'0': ({}, None)}))

        cal.sync_events(Event.pending_events.all())

        event.refresh_from_db()
        self.assertEqual(event.status, Event.ON_CAL)
        kwargs = cal.service.events.return_value.update.call_args.kwargs
        self.assertEqual(kwargs['calendarId'], 'cal-id')
        self.assertEqual(kwargs['eventId'], 'goog-7')

    def test_an_approved_deletion_removes_the_row(self):
        event = self._event(Event.DEL_APRV, google_id='goog-9')
        cal = self._calendar(FakeBatch({'0': (None, None)}))

        cal.sync_events(Event.pending_events.all())

        self.assertFalse(Event.objects.filter(pk=event.pk).exists())
        kwargs = cal.service.events.return_value.delete.call_args.kwargs
        self.assertEqual(kwargs['eventId'], 'goog-9')

    def test_one_failed_event_does_not_lose_the_others(self):
        for what in ['First', 'Second', 'Third']:
            self._event(Event.NEW_APRV, what=what)
        qs = Event.pending_events.all()
        # Don't assume the manager's ordering -- ask it which one is in the
        # middle, then fail exactly that one.
        middle = list(qs)[1]

        responses = {}
        for n, event in enumerate(qs):
            if event.pk == middle.pk:
                responses[str(n)] = (None, ValueError('Google said no'))
            else:
                responses[str(n)] = ({'id': 'g%d' % n,
                                      'htmlLink': 'u%d' % n}, None)
        cal = self._calendar(FakeBatch(responses))

        with patch.object(Event, 'notify_on_calendar'):
            with self.assertRaises(CalendarError) as cm:
                cal.sync_events(qs)

        self.assertIn(middle.what, str(cm.exception))
        self.assertIn('Google said no', str(cm.exception))

        middle.refresh_from_db()
        self.assertEqual(middle.status, Event.NEW_APRV)
        survivors = Event.objects.exclude(pk=middle.pk)
        self.assertEqual(survivors.count(), 2)
        for event in survivors:
            self.assertEqual(event.status, Event.ON_CAL)
            self.assertTrue(event.google_id)

    def test_a_pre_2015_event_is_addressed_by_its_bare_id(self):
        """Those rows hold a feed URL; Google answers 404 if we send it back."""
        feed_url = ('https://www.google.com/calendar/feeds/cal%40group.calendar'
                    '.google.com/private/full/vsi6l3v6stv0pj649t51k30b40')
        self._event(Event.EDIT_APRV, google_id=feed_url)
        cal = self._calendar(FakeBatch({'0': ({}, None)}))

        cal.sync_events(Event.pending_events.all())

        kwargs = cal.service.events.return_value.update.call_args.kwargs
        self.assertEqual(kwargs['eventId'], 'vsi6l3v6stv0pj649t51k30b40')

    def test_a_pre_2015_event_is_deleted_by_its_bare_id(self):
        feed_url = ('https://www.google.com/calendar/feeds/cal%40group.calendar'
                    '.google.com/private/full/rl1dch8sb0amg3bi5pda1jeiog')
        self._event(Event.DEL_APRV, google_id=feed_url)
        cal = self._calendar(FakeBatch({'0': (None, None)}))

        cal.sync_events(Event.pending_events.all())

        kwargs = cal.service.events.return_value.delete.call_args.kwargs
        self.assertEqual(kwargs['eventId'], 'rl1dch8sb0amg3bi5pda1jeiog')

    def test_an_unsyncable_status_is_refused(self):
        self._event(Event.NEW)
        batch = FakeBatch()
        cal = self._calendar(batch)

        with self.assertRaises(CalendarError) as cm:
            cal.sync_events(Event.objects.all())

        self.assertIn(str(Event.NEW), str(cm.exception))
        self.assertEqual(batch.added, [], msg='nothing should have been queued')

    def test_a_failed_batch_is_a_calendar_error(self):
        self._event(Event.NEW_APRV)
        cal = self._calendar(FakeBatch(execute_error=OSError('connection reset')))

        with self.assertRaises(CalendarError) as cm:
            cal.sync_events(Event.pending_events.all())

        self.assertIn('connection reset', str(cm.exception))
