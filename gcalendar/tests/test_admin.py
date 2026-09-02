"""Tests for the admin's Google sync page.

The page is the only way an approved event reaches the calendar, and the only
place a sync failure is reported. What matters here is that a bad or missing
credentials file is reported *in the page*: this view is where a member's
approved event either goes out or silently does not.

"""
import datetime
import os
import tempfile

from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse

from gcalendar.models import Event


class GoogleSyncViewTestCase(TestCase):

    def setUp(self):
        self.user = User.objects.create_superuser('admin', 'admin@example.com',
                                                  'pw')
        self.assertTrue(self.client.login(username='admin', password='pw'))
        self.url = reverse('admin:gcalendar-google_sync')

    def _event(self, status):
        return Event.objects.create(user=self.user, what='An Event',
                                    status=status, where='The Beach',
                                    start_date=datetime.date(2026, 7, 4),
                                    end_date=datetime.date(2026, 7, 4))

    def test_the_page_lists_the_events_waiting_to_go_out(self):
        self._event(Event.NEW_APRV)
        self._event(Event.NEW)          # not approved: must not be listed

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual([e.pk for e in response.context['events']],
                         [e.pk for e in Event.pending_events.all()])
        self.assertEqual(len(response.context['events']), 1)

    @override_settings(GCAL_CREDENTIALS_PATH='/no/such/service-account.json')
    def test_an_unreadable_key_is_reported_in_the_page(self):
        """Not a 500. The whole point of raising CalendarError is that the
        person who pressed the button is told what went wrong.

        """
        event = self._event(Event.NEW_APRV)

        response = self.client.post(self.url, {'synchronize': 'Synchronize Events'})

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['err_msg'])
        self.assertIn('/no/such/service-account.json', response.context['err_msg'])
        event.refresh_from_db()
        self.assertEqual(event.status, Event.NEW_APRV)

    def test_a_readable_credentials_file_shows_as_present(self):
        """cred_status is what gates the Synchronize button in the template."""
        fd, path = tempfile.mkstemp(suffix='.json')
        os.close(fd)
        self.addCleanup(os.remove, path)
        self._event(Event.NEW_APRV)

        with override_settings(GCAL_CREDENTIALS_PATH=path):
            response = self.client.get(self.url)

        self.assertIsNotNone(response.context['cred_status'])
        self.assertContains(response, 'Synchronize Events')
