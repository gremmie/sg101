"""Tests that removed dead/disabled code stays gone.

The `irc`, `legacy`, `membermap`, `custom_search` and `shoutbox` apps (and the
disabled Xapian/Haystack search stack) were removed; the shouts are archived
under `archive/shoutbox/`. These assertions fail loudly if any
of them get reintroduced -- e.g. an app slipped back into INSTALLED_APPS, or a
URL include resurrected.

Search is the one thing that came back, rebuilt on PostgreSQL rather than
resurrected: both its URLs serve real views again, covered by the `search` app's
own tests. Only `custom_search` itself has to stay gone.
"""
from django.apps import apps
from django.conf import settings
from django.urls import NoReverseMatch, reverse
from django.test import TestCase


REMOVED_APPS = ['irc', 'legacy', 'membermap', 'custom_search', 'shoutbox']


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
        for path in ['/irc/', '/member_map/', '/shout/', '/shout/view/history/']:
            self.assertEqual(self.client.get(path).status_code, 404,
                             msg='%s should no longer resolve' % path)

    def test_removed_url_names_are_gone(self):
        for name in ['irc-main', 'membermap-index', 'shoutbox-history', 'shoutbox-shout']:
            with self.assertRaises(NoReverseMatch):
                reverse(name)
