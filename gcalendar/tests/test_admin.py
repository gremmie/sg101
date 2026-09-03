"""Tests for the admin's Google sync page and its approval action.

The page is the only way an approved event reaches the calendar, and the only
place a sync failure is reported. What matters here is that a failure is
reported *in the page*: this view is where a member's approved event either
goes out or silently does not.

The approval action is the step before it. It ratchets an event forward and
awards a badge, and it is driven here through the changelist the way a person
drives it -- a direct call to the method would pass just as well with the action
unregistered.

"""
import datetime
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import NoReverseMatch, reverse

import bio.badges
from bio.models import Badge, BadgeOwnership
from gcalendar.calendar import CalendarError
from gcalendar.models import Event


class GoogleSyncViewTestCase(TestCase):

    def setUp(self):
        self.user = User.objects.create_superuser('admin', 'admin@example.com',
                                                  'pw')
        self.assertTrue(self.client.login(username='admin', password='pw'))
        self.url = reverse('admin:gcalendar-google_sync')

    def _event(self, status, what='An Event'):
        return Event.objects.create(user=self.user, what=what,
                                    status=status, where='The Beach',
                                    start_date=datetime.date(2026, 7, 4),
                                    end_date=datetime.date(2026, 7, 4))

    def test_the_page_selects_the_events_waiting_to_go_out(self):
        self._event(Event.NEW_APRV, what='Approved Gig')
        self._event(Event.NEW, what='Unapproved Gig')   # must not be listed

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual([e.pk for e in response.context['events']],
                         [e.pk for e in Event.pending_events.all()])
        self.assertEqual(len(response.context['events']), 1)

    def test_the_page_renders_the_events_it_selected(self):
        """Separate from the queryset above so that each assertion is reached
        under a mutation of the other: what the view picks and what the page
        shows are two claims.

        """
        self._event(Event.NEW_APRV, what='Approved Gig')
        self._event(Event.NEW, what='Unapproved Gig')

        response = self.client.get(self.url)

        self.assertContains(response, 'Approved Gig')
        self.assertNotContains(response, 'Unapproved Gig')

    @override_settings(GCAL_CREDENTIALS_PATH='/no/such/service-account.json')
    def test_an_unreadable_key_is_reported_in_the_page(self):
        """Not a 500. The whole point of raising CalendarError is that the
        person who pressed the button is told what went wrong.

        """
        event = self._event(Event.NEW_APRV, what='Approved Gig')

        response = self.client.post(self.url, {'synchronize': 'Synchronize Events'})

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['err_msg'])
        self.assertIn('/no/such/service-account.json', response.context['err_msg'])
        # The event has not gone anywhere, and is still listed to try again.
        event.refresh_from_db()
        self.assertEqual(event.status, Event.NEW_APRV)
        self.assertContains(response, 'Approved Gig')

    @override_settings(GCAL_CALENDAR_ID='cal-id',
                       GCAL_CREDENTIALS_PATH='/keys/sa.json')
    @patch('gcalendar.admin.Calendar')
    def test_a_clean_sync_reports_success(self, mock_calendar):
        self._event(Event.NEW_APRV, what='Approved Gig')

        response = self.client.post(self.url, {'synchronize': 'Synchronize Events'})

        self.assertEqual(response.status_code, 200)
        mock_calendar.assert_called_once_with(calendar_id='cal-id',
                                             credentials_path='/keys/sa.json')
        self.assertTrue(mock_calendar.return_value.sync_events.called)
        self.assertContains(response, 'All events processed successfully.')
        self.assertEqual(response.context['err_msg'], '')
        self.assertNotContains(response, 'errorlist')
        self.assertEqual(len(response.context['events']), 0)

    @patch('gcalendar.admin.Calendar')
    def test_a_sync_failure_is_rendered_not_raised(self, mock_calendar):
        """A CalendarError out of sync_events is Google refusing an event,
        rather than the key being unreadable. It reaches the same place.

        """
        mock_calendar.return_value.sync_events.side_effect = CalendarError(
                'An Event - the calendar said no')
        self._event(Event.NEW_APRV, what='Approved Gig')

        response = self.client.post(self.url, {'synchronize': 'Synchronize Events'})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'the calendar said no')
        self.assertEqual(len(response.context['events']), 1)
        self.assertContains(response, 'Approved Gig')

    @override_settings(GCAL_CREDENTIALS_PATH='')
    def test_the_page_carries_no_credentials_furniture(self):
        """A service account key does not expire, so there is no status to
        report and nothing to re-request. The button no longer waits on a file
        being there: with no key configured, pressing it reports that.

        """
        self._event(Event.NEW_APRV, what='Approved Gig')

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Synchronize Events')
        self.assertNotContains(response, 'Credentials file status')
        self.assertNotContains(response, 'Request new credentials')

    def test_the_authorization_routes_are_gone(self):
        """The sync route is asserted alongside them: dropping every custom URL
        would satisfy the two NoReverseMatch assertions perfectly.

        """
        for name in ('admin:gcalendar-authorize', 'admin:gcalendar-auth_return'):
            with self.subTest(name=name), self.assertRaises(NoReverseMatch):
                reverse(name)

        self.assertTrue(reverse('admin:gcalendar-google_sync'))


class ApproveEventsTestCase(TestCase):
    """The action that moves an event into the queue the sync page pushes."""

    def setUp(self):
        self.user = User.objects.create_superuser('admin', 'admin@example.com',
                                                  'pw')
        self.assertTrue(self.client.login(username='admin', password='pw'))
        self.url = reverse('admin:gcalendar_event_changelist')
        # award_badge only logs and returns when the row is missing, so without
        # this the badge assertions below would pass while proving nothing.
        self.badge = Badge.objects.create(name='Calendar Pin', order=1,
                                          numeric_id=bio.badges.CALENDAR_PIN)

    def _event(self, status):
        return Event.objects.create(user=self.user, what='An Event',
                                    status=status, where='The Beach',
                                    start_date=datetime.date(2026, 7, 4),
                                    end_date=datetime.date(2026, 7, 4))

    def _approve(self, *events):
        return self.client.post(self.url, {
            'action': 'approve_events',
            'index': 0,
            '_selected_action': [str(e.pk) for e in events],
        }, follow=True)

    def _badge_count(self):
        try:
            return BadgeOwnership.objects.get(profile=self.user.profile,
                                              badge=self.badge).count
        except BadgeOwnership.DoesNotExist:
            return 0

    def test_approval_ratchets_each_pending_state_forward(self):
        new = self._event(Event.NEW)
        edit = self._event(Event.EDIT_REQ)
        delete = self._event(Event.DEL_REQ)

        response = self._approve(new, edit, delete)

        for event, expected in ((new, Event.NEW_APRV),
                                (edit, Event.EDIT_APRV),
                                (delete, Event.DEL_APRV)):
            with self.subTest(status=event.status):
                event.refresh_from_db()
                self.assertEqual(event.status, expected)
        self.assertContains(response, '3 events were approved.')

    def test_only_a_new_event_earns_the_calendar_pin(self):
        """All three belong to the same member, so a count of one is what says
        the edit and delete approvals did not award anything.

        """
        self._approve(self._event(Event.NEW),
                      self._event(Event.EDIT_REQ),
                      self._event(Event.DEL_REQ))

        self.assertEqual(self._badge_count(), 1)

    def test_the_message_is_singular_for_one_event(self):
        response = self._approve(self._event(Event.NEW))

        self.assertContains(response, '1 event was approved.')

    def test_an_event_already_on_the_calendar_is_left_alone(self):
        event = self._event(Event.ON_CAL)

        response = self._approve(event)

        event.refresh_from_db()
        self.assertEqual(event.status, Event.ON_CAL)
        self.assertContains(response, '0 events were approved.')
        self.assertEqual(self._badge_count(), 0)
