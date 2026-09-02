"""Tests for the gcalendar models."""
import datetime

from django.contrib.auth.models import User
from django.test import TestCase

from gcalendar.models import Event


FEED_URL = ('https://www.google.com/calendar/feeds/'
            'i81lu3fkh57sgqqenogefd9v78%40group.calendar.google.com/'
            'private/full/vsi6l3v6stv0pj649t51k30b40')


class GoogleEventIdTestCase(TestCase):
    """google_id is stored in two formats, and only one of them is an event id."""

    def setUp(self):
        self.user = User.objects.create_user('brian', 'brian@example.com', 'pw')

    def _event(self, google_id):
        return Event.objects.create(user=self.user, what='An Event',
                                    status=Event.ON_CAL, google_id=google_id,
                                    start_date=datetime.date(2014, 7, 4),
                                    end_date=datetime.date(2014, 7, 4))

    def test_a_feed_url_yields_the_id_at_the_end_of_it(self):
        event = self._event(FEED_URL)
        self.assertEqual(event.google_event_id, 'vsi6l3v6stv0pj649t51k30b40')

    def test_an_id_that_is_already_bare_is_unchanged(self):
        event = self._event('n1oo2ov00dtv5o082p1rhlbiuc')
        self.assertEqual(event.google_event_id, 'n1oo2ov00dtv5o082p1rhlbiuc')

    def test_an_event_that_never_reached_google_has_no_id(self):
        """A NEW event has google_id='' and must not become something else."""
        self.assertEqual(self._event('').google_event_id, '')
