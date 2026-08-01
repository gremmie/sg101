"""Tests that removed dead/disabled code stays gone.

The `irc`, `legacy`, `membermap`, and `custom_search` apps (and the disabled
Xapian/Haystack search stack) were removed. These assertions fail loudly if any
of them get reintroduced -- e.g. an app slipped back into INSTALLED_APPS, or a
URL include resurrected.
"""
from django.apps import apps
from django.conf import settings
from django.urls import NoReverseMatch, reverse
from django.test import TestCase


REMOVED_APPS = ['irc', 'legacy', 'membermap', 'custom_search']


class PrunedAppsTests(TestCase):

    def test_removed_apps_not_installed(self):
        for label in REMOVED_APPS:
            self.assertNotIn(
                label, settings.INSTALLED_APPS,
                msg='%r should have been removed from INSTALLED_APPS' % label)
            self.assertFalse(
                apps.is_installed(label),
                msg='%r should not be an installed app' % label)

    def test_removed_urls_return_404(self):
        for path in ['/irc/', '/member_map/']:
            self.assertEqual(self.client.get(path).status_code, 404,
                             msg='%s should no longer resolve' % path)

    def test_removed_url_names_are_gone(self):
        for name in ['irc-main', 'membermap-index']:
            with self.assertRaises(NoReverseMatch):
                reverse(name)

    def test_quick_search_stub_still_serves(self):
        # The search page itself is no longer stubbed -- it runs on Postgres
        # full-text search now, and search/tests/test_views.py covers it. The
        # forums' duplicate-topic quick search is still waiting on its view, so
        # its URL must keep resolving.
        self.assertEqual(self.client.get('/search/ajax/').status_code, 200)
