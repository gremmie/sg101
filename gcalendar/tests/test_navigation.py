"""Tests that the site's navigation still points at the calendar.

The link was removed from both base templates in 2023, while the sync was
broken, and `/calendar/` was unreachable from anywhere on the site for three
years. These render real pages rather than reading the templates as text,
because a `{% url %}` naming a route that no longer exists raises
`NoReverseMatch` at *render* time -- an import-level or string-level check sees
nothing, and the page 500s in a browser.

The site runs two live designs and both need the link: the forums and flatpages
still use `base.html`, everything else uses `v3/base.html`.

"""
from django.test import TestCase
from django.urls import reverse


class CalendarNavigationTestCase(TestCase):

    def _assert_links_to_the_calendar(self, url_name):
        response = self.client.get(reverse(url_name))

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            '<a href="%s">Calendar</a>' % reverse('gcalendar-index'),
            html=True)

    def test_the_forums_design_links_to_the_calendar(self):
        """`base.html`, still worn by the busiest part of the site."""
        self._assert_links_to_the_calendar('forums-index')

    def test_the_v3_design_links_to_the_calendar(self):
        """`v3/base.html`, worn by everything else, the home page included."""
        self._assert_links_to_the_calendar('home')
