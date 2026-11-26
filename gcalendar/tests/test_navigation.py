"""Tests that the site's navigation still points at the calendar.

The link was removed from both base templates in 2023, while the sync was
broken, and `/calendar/` was unreachable from anywhere on the site for three
years. These render real pages rather than reading the templates as text,
because a `{% url %}` naming a route that no longer exists raises
`NoReverseMatch` at *render* time -- an import-level or string-level check sees
nothing, and the page 500s in a browser.

Every page wears `v3/base.html`, so the home page stands for the site's menu.

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

    def test_the_menu_links_to_the_calendar(self):
        self._assert_links_to_the_calendar('home')
