"""Tests for the member-facing half of the calendar.

The admin tests cover the staff half -- approving an event and pushing it to
Google. These cover the half a member drives: reading the calendar, submitting
an event, listing their own, changing one and deleting one. Nothing in the
member's path applies a change directly; every write asks the staff for
something, and what these assert is which state each view leaves behind.

Two of them are characterization rather than design. `edit_events` lists only
events already on the calendar, so a member cannot reach one they just
submitted -- but `edit_event` filters on nothing, so a kept URL still works.
Both are pinned here as they stand.

Every POST carries a `time_zone`. The field is `required=False` and its
validator rejects the empty string, so a payload missing it comes back as a
200 with errors; a test asserting only on the status code would pass against a
view that saved nothing.

"""
import datetime

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse

from gcalendar.models import Event


class CalendarTestCase(TestCase):
    """A logged-in member, and the shapes the pages deal in."""

    def setUp(self):
        self.user = User.objects.create_user('brian', 'brian@example.com', 'pw')
        self.other = User.objects.create_user('ivan', 'ivan@example.com', 'pw')
        self.assertTrue(self.client.login(username='brian', password='pw'))

    def _event(self, user=None, **overrides):
        fields = {
            'user': user or self.user,
            'what': 'An Event',
            'status': Event.ON_CAL,
            'where': 'The Beach',
            'start_date': datetime.date(2026, 7, 4),
            'end_date': datetime.date(2026, 7, 4),
            'start_time': datetime.time(19, 0),
            'end_time': datetime.time(22, 0),
        }
        fields.update(overrides)
        return Event.objects.create(**fields)

    def _payload(self, **overrides):
        data = {
            'what': 'Surf Night at the Tiki Lounge',
            'start_date': '07/04/2026',
            'start_time': '19:00',
            'end_date': '07/04/2026',
            'end_time': '22:00',
            'time_zone': 'America/New_York',
            'where': '123 Beach Road, Santa Cruz, CA',
            'description': 'Three bands, **one** night.',
        }
        data.update(overrides)
        return {k: v for k, v in data.items() if v is not None}

    def _assert_login_is_required(self, url):
        self.client.logout()

        response = self.client.get(url)

        self.assertRedirects(response,
                             '%s?next=%s' % (reverse('accounts-login'), url))


class IndexTestCase(CalendarTestCase):
    """The calendar page itself, which is an embedded Google iframe.

    The time zone is not decorative: it is interpolated into the embed's `ctz`
    parameter and decides what times the iframe displays. So these assert on
    the rendered URL rather than on the context value that feeds it.

    """
    def setUp(self):
        super().setUp()
        self.url = reverse('gcalendar-index')

    def test_the_page_shows_the_members_own_time_zone(self):
        profile = self.user.profile
        profile.time_zone = 'America/New_York'
        profile.save()

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'ctz=America%2FNew_York')

    def test_the_page_shows_pacific_time_to_a_visitor(self):
        """There is no profile to read, so the view names a zone in the code."""
        self.client.logout()

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'ctz=US%2FPacific')


class AddEventTestCase(CalendarTestCase):

    def setUp(self):
        super().setUp()
        self.url = reverse('gcalendar-add')

    def test_login_is_required(self):
        self._assert_login_is_required(self.url)

    def test_a_submitted_event_is_stored_as_new_and_owned_by_the_submitter(self):
        response = self.client.post(self.url, self._payload())

        self.assertRedirects(response, self.url + '?thanks=1')
        event = Event.objects.get()
        self.assertEqual(event.user, self.user)
        self.assertEqual(event.status, Event.NEW)

    def test_the_submitted_values_are_stored(self):
        """Separate from the test above because "a row appeared, owned by the
        right member" and "the row holds what was typed" are two claims, and
        the second is the one that catches a save path dropping a field.

        """
        self.client.post(self.url, self._payload())

        event = Event.objects.get()
        self.assertEqual(event.what, 'Surf Night at the Tiki Lounge')
        self.assertEqual(event.where, '123 Beach Road, Santa Cruz, CA')
        self.assertEqual(event.start_date, datetime.date(2026, 7, 4))
        self.assertEqual(event.end_date, datetime.date(2026, 7, 4))
        self.assertEqual(event.start_time, datetime.time(19, 0))
        self.assertEqual(event.end_time, datetime.time(22, 0))
        self.assertEqual(event.time_zone, 'America/New_York')
        self.assertFalse(event.all_day)
        self.assertEqual(event.description, 'Three bands, **one** night.')

    def test_the_description_is_stored_as_rendered_html(self):
        """The page renders `html`, never `description`, so a submission that
        stored only the source text would show as an empty event.

        `add_event` passes the form's already-rendered markup to `save()` while
        `edit_event` lets the model render it again -- but both call
        `site_markup` with the same arguments, so no assertion can tell the two
        paths apart and none here claims to.

        """
        self.client.post(self.url, self._payload())

        self.assertEqual(Event.objects.get().html,
                         '<p>Three bands, <strong>one</strong> night.</p>')

    def test_a_forum_thread_can_be_asked_for(self):
        self.client.post(self.url, self._payload(create_forum_thread='on'))

        self.assertTrue(Event.objects.get().create_forum_thread)

    def test_an_invalid_time_zone_redisplays_the_form_and_saves_nothing(self):
        response = self.client.post(self.url, self._payload(time_zone=None))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Invalid timezone.')
        self.assertFalse(Event.objects.exists())

    def test_an_end_before_its_start_redisplays_the_form_and_saves_nothing(self):
        response = self.client.post(self.url,
                                    self._payload(end_date='07/03/2026'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'is after the ending time!')
        self.assertFalse(Event.objects.exists())

    def test_the_thanks_message_is_shown_after_the_redirect(self):
        response = self.client.post(self.url, self._payload(), follow=True)

        self.assertContains(response, 'Thanks for submitting an event')

    def test_the_empty_form_carries_no_thanks_message(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Thanks for submitting an event')


class EditEventsTestCase(CalendarTestCase):
    """The member's list of their own events."""

    def setUp(self):
        super().setUp()
        self.url = reverse('gcalendar-edit_events')

    def test_login_is_required(self):
        self._assert_login_is_required(self.url)

    def test_only_the_members_own_events_are_listed(self):
        mine = self._event(what='My Gig')
        self._event(user=self.other, what='Ivan\'s Gig')

        response = self.client.get(self.url)

        self.assertEqual([e.pk for e in response.context['page'].object_list],
                         [mine.pk])
        self.assertContains(response, 'My Gig')
        self.assertNotContains(response, 'Ivan&#x27;s Gig')

    def test_an_event_not_yet_on_the_calendar_is_not_listed(self):
        """Characterization, and the one that surprises: a member cannot see
        an event they have just submitted, because the list filters on
        `ON_CAL` and a new one is `NEW` until the staff push it out.

        """
        self._event(what='Waiting Gig', status=Event.NEW)

        response = self.client.get(self.url)

        self.assertEqual(list(response.context['page'].object_list), [])
        self.assertContains(response, 'You either have no events')

    def test_a_page_past_the_end_is_a_404(self):
        self._event()

        response = self.client.get(self.url, {'page': 99})

        self.assertEqual(response.status_code, 404)

    def test_a_page_that_is_not_a_number_falls_back_to_the_first(self):
        event = self._event()

        response = self.client.get(self.url, {'page': 'last'})

        self.assertEqual(response.status_code, 200)
        self.assertEqual([e.pk for e in response.context['page'].object_list],
                         [event.pk])

    def test_the_thanks_message_is_shown_after_an_edit(self):
        response = self.client.get(self.url, {'thanks': 1})

        self.assertContains(response, 'Thanks for updating your event')


class EditEventTestCase(CalendarTestCase):
    """Changing one event. Nothing here reaches Google: an edit asks the staff
    to make the change, and the row records that it was asked.

    """
    def setUp(self):
        super().setUp()
        self.event = self._event()
        self.url = reverse('gcalendar-edit_event', args=[self.event.pk])

    def test_login_is_required(self):
        self._assert_login_is_required(self.url)

    def test_the_form_opens_on_the_events_current_values(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'An Event')
        self.assertContains(response, 'The Beach')

    def test_a_change_is_requested_rather_than_applied(self):
        response = self.client.post(self.url, self._payload(what='A New Name'))

        self.assertRedirects(response,
                             reverse('gcalendar-edit_events') + '?thanks=1')
        self.event.refresh_from_db()
        self.assertEqual(self.event.what, 'A New Name')
        self.assertEqual(self.event.status, Event.EDIT_REQ)

    def test_the_edited_values_are_stored(self):
        self.client.post(self.url, self._payload(where='The Other Beach',
                                                 end_time='23:30'))

        self.event.refresh_from_db()
        self.assertEqual(self.event.where, 'The Other Beach')
        self.assertEqual(self.event.end_time, datetime.time(23, 30))
        self.assertEqual(self.event.time_zone, 'America/New_York')
        self.assertEqual(self.event.html,
                         '<p>Three bands, <strong>one</strong> night.</p>')

    def test_an_invalid_change_redisplays_the_form_and_stores_nothing(self):
        response = self.client.post(self.url, self._payload(what='A New Name',
                                                            time_zone=None))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Invalid timezone.')
        self.event.refresh_from_db()
        self.assertEqual(self.event.what, 'An Event')
        self.assertEqual(self.event.status, Event.ON_CAL)

    def test_an_event_with_no_times_can_be_opened(self):
        """Times are nullable and the oldest events have them unset. The form
        formatted them unconditionally, so the page 500'd on an event the
        member's own list had offered them a link to.

        """
        event = self._event(start_time=None, end_time=None)

        response = self.client.get(
                reverse('gcalendar-edit_event', args=[event.pk]))

        self.assertEqual(response.status_code, 200)

    def test_an_event_that_is_not_on_the_calendar_cannot_be_edited(self):
        """The list shows only events on the calendar, and this is the same
        rule: an event waiting on the staff is not the member's to change.

        """
        for status in (Event.NEW, Event.EDIT_REQ, Event.DEL_REQ):
            with self.subTest(status=status):
                event = self._event(status=status)
                url = reverse('gcalendar-edit_event', args=[event.pk])

                self.assertEqual(self.client.get(url).status_code, 404)

                self.assertEqual(
                        self.client.post(url, self._payload()).status_code, 404)
                event.refresh_from_db()
                self.assertEqual(event.status, status)

    def test_an_approved_event_cannot_be_taken_out_of_the_sync_queue(self):
        """The reason the rule is enforced here rather than only in the list.
        An approved event is waiting for the admin sync page to push it, and
        `edit_event` sets `EDIT_REQ` whatever the status was -- so a member
        posting from a URL they still had would drop it out of
        `Event.pending_events` with nothing said.

        """
        event = self._event(status=Event.EDIT_APRV)

        response = self.client.post(
                reverse('gcalendar-edit_event', args=[event.pk]),
                self._payload())

        self.assertEqual(response.status_code, 404)
        event.refresh_from_db()
        self.assertEqual(event.status, Event.EDIT_APRV)
        self.assertIn(event, Event.pending_events.all())

    def test_another_members_event_cannot_be_read(self):
        url = reverse('gcalendar-edit_event',
                      args=[self._event(user=self.other).pk])

        self.assertEqual(self.client.get(url).status_code, 403)

    def test_another_members_event_cannot_be_written(self):
        event = self._event(user=self.other)
        url = reverse('gcalendar-edit_event', args=[event.pk])

        response = self.client.post(url, self._payload(what='A New Name'))

        self.assertEqual(response.status_code, 403)
        event.refresh_from_db()
        self.assertEqual(event.what, 'An Event')
        self.assertEqual(event.status, Event.ON_CAL)

    def test_an_event_that_does_not_exist_is_a_404(self):
        url = reverse('gcalendar-edit_event', args=[self.event.pk + 1000])

        self.assertEqual(self.client.get(url).status_code, 404)


class DeleteEventTestCase(CalendarTestCase):
    """The AJAX endpoint behind the x on the member's list.

    It deletes nothing: it marks the event for the staff to delete, and the
    row survives until they do. Its callers are hand-written, so it checks its
    own input and reports each refusal with a different status.

    """
    def setUp(self):
        super().setUp()
        self.event = self._event()
        self.url = reverse('gcalendar-delete')

    def test_an_event_is_marked_for_deletion_rather_than_deleted(self):
        response = self.client.post(self.url, {'id': self.event.pk})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode(), str(self.event.pk))
        self.event.refresh_from_db()
        self.assertEqual(self.event.status, Event.DEL_REQ)

    def test_the_reply_is_plain_text(self):
        """`gcalendar_edit.js` asks for `dataType: 'text'` and uses the body to
        find the row to fade out, so the id above is interface rather than a
        courtesy, and the content type is what carries it as one.

        """
        response = self.client.post(self.url, {'id': self.event.pk})

        self.assertEqual(response['Content-Type'], 'text/plain')

    def test_an_anonymous_post_is_forbidden(self):
        """This view is not decorated -- it answers 403 itself rather than
        redirecting, there being no page to send an XHR to.

        """
        self.client.logout()

        response = self.client.post(self.url, {'id': self.event.pk})

        self.assertEqual(response.status_code, 403)
        self.event.refresh_from_db()
        self.assertEqual(self.event.status, Event.ON_CAL)

    def test_another_members_event_cannot_be_deleted(self):
        event = self._event(user=self.other)

        response = self.client.post(self.url, {'id': event.pk})

        self.assertEqual(response.status_code, 403)
        event.refresh_from_db()
        self.assertEqual(event.status, Event.ON_CAL)

    def test_a_post_with_no_id_is_a_bad_request(self):
        self.assertEqual(self.client.post(self.url, {}).status_code, 400)

    def test_an_id_that_is_not_a_number_is_a_bad_request(self):
        response = self.client.post(self.url, {'id': 'abc'})

        self.assertEqual(response.status_code, 400)
        self.event.refresh_from_db()
        self.assertEqual(self.event.status, Event.ON_CAL)

    def test_an_id_matching_no_event_is_a_bad_request(self):
        response = self.client.post(self.url, {'id': self.event.pk + 1000})

        self.assertEqual(response.status_code, 400)


class DeleteEventCsrfTestCase(CalendarTestCase):
    """The delete is a bare XHR, and this is the pair that says its token
    arrives.

    `gcalendar_edit.js` posts `{id: ...}` and no `csrfmiddlewaretoken`. What
    supplies the token is `v3/base.html` loading `js/v3/sg101.js`, whose global
    `$.ajaxSetup` puts the `csrftoken` cookie into an `X-CSRFToken` header on
    every relative request. The page carrying the delete button sets that
    cookie itself, so the sequence below is the one a browser performs: load
    the list, then post the id with the cookie's value as the header.

    """
    def setUp(self):
        super().setUp()
        self.client = Client(enforce_csrf_checks=True)
        self.assertTrue(self.client.login(username='brian', password='pw'))
        self.event = self._event()
        self.url = reverse('gcalendar-delete')

    def test_the_delete_the_page_sends_is_accepted(self):
        self.client.get(reverse('gcalendar-edit_events'))
        token = self.client.cookies['csrftoken'].value

        response = self.client.post(self.url, {'id': self.event.pk},
                                    HTTP_X_CSRFTOKEN=token)

        self.assertEqual(response.status_code, 200)
        self.event.refresh_from_db()
        self.assertEqual(self.event.status, Event.DEL_REQ)

    def test_a_post_without_the_header_is_rejected(self):
        response = self.client.post(self.url, {'id': self.event.pk})

        self.assertEqual(response.status_code, 403)
        self.event.refresh_from_db()
        self.assertEqual(self.event.status, Event.ON_CAL)
