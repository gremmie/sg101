"""Tests for the member's event submission form.

`EventEntryForm` carries three rules that live nowhere else: the hidden time
zone the page's two select boxes write into, a cross-field check that an event
does not end before it begins, and the removal of the forum-thread checkbox
once the event exists. Each of them has a way of passing silently -- the time
zone is `required=False` yet cannot be empty, the cross-field check is guarded
by fields that are themselves optional, and a field deleted from the form looks
exactly like one that was never declared.

The form also prefills an existing event's dates and times in the format the
jQuery UI datepicker and the hour selects expect, which is the only reason the
edit page can round-trip a value it rendered.

"""
import datetime

from django.contrib.auth.models import User
from django.test import TestCase

from gcalendar.forms import EventEntryForm
from gcalendar.models import Event


class FormTestCase(TestCase):
    """Holds the submission the page produces, for the cases to bend."""

    def _payload(self, **overrides):
        """A valid submission. An override of None drops the key entirely,
        which is how a field the browser did not fill in arrives.

        """
        data = {
            'what': 'Surf Night at the Tiki Lounge',
            'start_date': '07/04/2026',
            'start_time': '19:00',
            'end_date': '07/04/2026',
            'end_time': '22:00',
            'time_zone': 'US/Pacific',
            'where': '123 Beach Road, Santa Cruz, CA',
            'description': 'Three bands, one night.',
        }
        data.update(overrides)
        return {k: v for k, v in data.items() if v is not None}


class TimeZoneValidationTestCase(FormTestCase):
    """`clean_time_zone` hands its input to `ZoneInfo`, which has two ways of
    saying no. Both reach the member as the same message, so the cases are
    separated by what they submit rather than by what they read.

    """
    def test_an_absent_time_zone_is_rejected(self):
        """The field is `required=False`, so an unfilled one is never reported
        as missing: it arrives as `''`, and `ZoneInfo('')` raises `ValueError`
        rather than `ZoneInfoNotFoundError`.

        """
        form = EventEntryForm(self._payload(time_zone=None))

        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors['time_zone'], ['Invalid timezone.'])

    def test_an_unknown_time_zone_is_rejected(self):
        form = EventEntryForm(self._payload(time_zone='Bogus/Zone'))

        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors['time_zone'], ['Invalid timezone.'])

    def test_a_real_time_zone_is_accepted(self):
        form = EventEntryForm(self._payload(time_zone='America/New_York'))

        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data['time_zone'], 'America/New_York')


class CrossFieldValidationTestCase(FormTestCase):

    ERROR = 'The start date of the event is after the ending time!'

    def test_an_event_that_ends_before_it_starts_is_rejected(self):
        form = EventEntryForm(self._payload(start_time='22:00',
                                            end_time='19:00'))

        self.assertFalse(form.is_valid())
        self.assertEqual(form.non_field_errors(), [self.ERROR])

    def test_an_event_that_ends_the_day_before_it_starts_is_rejected(self):
        """The dates are compared too, not only the hours."""
        form = EventEntryForm(self._payload(end_date='07/03/2026'))

        self.assertFalse(form.is_valid())
        self.assertEqual(form.non_field_errors(), [self.ERROR])

    def test_an_all_day_event_is_compared_by_date(self):
        form = EventEntryForm(self._payload(all_day='on',
                                            end_date='07/03/2026'))

        self.assertFalse(form.is_valid())
        self.assertEqual(form.non_field_errors(), [self.ERROR])

    def test_an_all_day_event_with_no_start_time_is_still_compared(self):
        """The times are optional and the check once required them, so an
        event ending the day before it began validated cleanly whenever one was
        missing -- and for an all-day event the times are not even part of the
        comparison it was skipping.

        """
        form = EventEntryForm(self._payload(all_day='on', start_time=None,
                                            end_date='07/03/2026'))

        self.assertFalse(form.is_valid())
        self.assertEqual(form.non_field_errors(), [self.ERROR])

    def test_a_timed_event_with_no_times_is_compared_by_date(self):
        """Neither hour was given, so the dates are all there is to compare."""
        form = EventEntryForm(self._payload(start_time=None, end_time=None,
                                            end_date='07/03/2026'))

        self.assertFalse(form.is_valid())
        self.assertEqual(form.non_field_errors(), [self.ERROR])

    def test_an_event_with_no_times_on_one_day_is_accepted(self):
        """The companion: comparing the dates must not reject an event whose
        ordering the missing times leave nothing to object to.

        """
        form = EventEntryForm(self._payload(start_time=None, end_time=None))

        self.assertTrue(form.is_valid(), form.errors)

    def test_an_event_with_only_a_start_time_is_compared_by_date(self):
        """An hour on one end and not the other cannot order two datetimes,
        and the same day with only a start time is not an error.

        """
        form = EventEntryForm(self._payload(end_time=None))

        self.assertTrue(form.is_valid(), form.errors)


class DescriptionTestCase(FormTestCase):
    """`clean_description` renders the markup and hangs it on the form, which
    is where `add_event` picks it up to save.

    """
    def test_the_description_is_rendered_for_the_view_to_save(self):
        form = EventEntryForm(
                self._payload(description='Three bands, **one** night.'))

        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.html,
                         '<p>Three bands, <strong>one</strong> night.</p>')

    def test_an_empty_description_renders_no_html(self):
        form = EventEntryForm(self._payload(description=None))

        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.html, '')

    def test_an_image_the_site_will_not_serve_is_rejected(self):
        """The check runs on the rendered markup rather than the source, so
        the way to reach it is to write markup that produces an `img`.

        """
        form = EventEntryForm(self._payload(
                description='![poster](http://example.com/poster.png)'))

        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors['description'],
                         ['Image must be accessed via https'])


class ExistingEventTestCase(TestCase):
    """The form as the edit page builds it, from an instance."""

    def setUp(self):
        self.user = User.objects.create_user('brian', 'brian@example.com', 'pw')

    def _event(self, **overrides):
        fields = {
            'user': self.user,
            'what': 'An Event',
            'status': Event.ON_CAL,
            'start_date': datetime.date(2026, 7, 4),
            'end_date': datetime.date(2026, 7, 5),
            # Neither hour is one of the form's defaults, so an assertion
            # that the instance's own times are prefilled can fail.
            'start_time': datetime.time(18, 30),
            'end_time': datetime.time(21, 30),
        }
        fields.update(overrides)
        return Event.objects.create(**fields)

    def test_an_existing_event_cannot_start_a_forum_thread(self):
        """The thread is created the first time the event reaches Google, so
        offering the checkbox again on an edit would offer nothing.

        """
        form = EventEntryForm(instance=self._event())

        self.assertNotIn('create_forum_thread', form.fields)

    def test_a_new_event_can_start_a_forum_thread(self):
        """The companion: deleting the field from every form would satisfy the
        assertion above on its own.

        """
        self.assertIn('create_forum_thread', EventEntryForm().fields)

    def test_the_dates_and_times_are_prefilled_for_the_page_widgets(self):
        form = EventEntryForm(instance=self._event())

        self.assertEqual(form.initial['start_date'], '07/04/2026')
        self.assertEqual(form.initial['end_date'], '07/05/2026')
        self.assertEqual(form.initial['start_time'], '18:30')
        self.assertEqual(form.initial['end_time'], '21:30')

    def test_an_all_day_event_is_prefilled_with_the_default_hours(self):
        """Its own hours are ignored -- the page hides the time selects when
        All Day is checked, and they still have to hold something.

        """
        form = EventEntryForm(instance=self._event(all_day=True,
                                                   start_time=datetime.time(9),
                                                   end_time=datetime.time(10)))

        self.assertEqual(form.initial['start_time'], '19:00')
        self.assertEqual(form.initial['end_time'], '20:00')

    def test_an_event_with_no_times_is_prefilled_with_the_default_hours(self):
        """Both time columns are nullable, and events predating this form have
        them unset. Formatting the missing value raised `AttributeError` while
        the form was being built, so the edit page answered a 500 for an event
        it had itself listed as editable.

        """
        form = EventEntryForm(instance=self._event(start_time=None,
                                                   end_time=None))

        self.assertEqual(form.initial['start_time'], '19:00')
        self.assertEqual(form.initial['end_time'], '20:00')


class NewEventTestCase(TestCase):

    def test_a_new_form_opens_on_today_at_the_house_hours(self):
        today = datetime.date.today().strftime('%m/%d/%Y')

        form = EventEntryForm()

        self.assertEqual(form.initial['start_date'], today)
        self.assertEqual(form.initial['end_date'], today)
        self.assertEqual(form.initial['start_time'], '19:00')
        self.assertEqual(form.initial['end_time'], '20:00')
