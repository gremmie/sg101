"""
Tests for the network seed data.

The seeding used to be a post_migrate receiver that re-ran on every migrate.
These cover what replaced it: that a fresh database gets the short list, that
an existing one is neither duplicated nor stripped of anything in use, and
that reversing takes nothing away.
"""
import importlib
import logging

from django.apps import apps as global_apps
from django.contrib.auth.models import User
from django.contrib.staticfiles import finders
from django.test import TestCase

from elsewhere.models import InstantMessenger
from elsewhere.models import InstantMessengerProfile
from elsewhere.models import SocialNetwork
from elsewhere.models import SocialNetworkProfile

seed = importlib.import_module('elsewhere.migrations.0004_seed_networks')

# Four of the 42 the receiver used to create, as a stand-in for all of them.
RETIRED = [
    ('pownce', 'Pownce', 'http://pownce.com/%s/', 'Username', 'pownce.png'),
    ('bebo', 'Bebo', 'http://www.bebo.com/Profile.jsp?MemberId=%s', 'Member ID', 'bebo.png'),
    ('orkut', 'Orkut', 'http://www.orkut.com/Profile.aspx?uid=%s', 'User ID', 'orkut.png'),
    ('jaiku', 'Jaiku', 'http://%s.jaiku.com', 'Username', 'jaiku.png'),
]


def _recreate_retired():
    for slug, name, url, identifier, icon in RETIRED:
        SocialNetwork.objects.create(slug=slug, name=name, url=url,
                                     identifier=identifier, icon=icon)


class SeededDataTests(TestCase):
    """What a freshly migrated database holds."""

    def test_only_the_networks_in_use_are_seeded(self):
        self.assertEqual(SocialNetwork.objects.count(), 15)
        self.assertEqual(InstantMessenger.objects.count(), 5)

    def test_no_post_migrate_receiver_remains(self):
        with self.assertRaises(ImportError):
            importlib.import_module('elsewhere.management')

    def test_every_social_url_is_https(self):
        for network in SocialNetwork.objects.all():
            with self.subTest(slug=network.slug):
                self.assertTrue(network.url.startswith('https://'), network.url)

    def test_the_stale_templates_were_refreshed(self):
        urls = dict(SocialNetwork.objects.values_list('slug', 'url'))

        self.assertEqual(urls['twitter'], 'https://x.com/%s')
        self.assertEqual(urls['pandora'], 'https://www.pandora.com/profile/%s')
        self.assertEqual(urls['foursquare'], 'https://foursquare.com/user?uid=%s')

    def test_every_network_has_a_slug_that_fits_network_id(self):
        # network_id is a CharField(max_length=16); a longer slug would be
        # unstorable on the profile row that has to point at it.
        width = SocialNetworkProfile._meta.get_field('network_id').max_length

        for model in (SocialNetwork, InstantMessenger):
            for network in model.objects.all():
                with self.subTest(slug=network.slug):
                    self.assertTrue(network.slug)
                    self.assertLessEqual(len(network.slug), width)

    def test_every_seeded_icon_file_exists(self):
        for model in (SocialNetwork, InstantMessenger):
            for network in model.objects.all():
                with self.subTest(slug=network.slug):
                    self.assertIsNotNone(
                        finders.find('elsewhere/' + network.icon),
                        'missing icon file for %s' % network.slug)

    def test_the_slugs_in_use_are_the_ones_members_already_stored(self):
        # Not round-tripped through slugify: these are the 15 values sitting in
        # 327 production rows, and every one of them has to keep resolving.
        self.assertEqual(
            set(SocialNetwork.objects.values_list('slug', flat=True)),
            {'facebook', 'twitter', 'youtube', 'myspace', 'tumblr', 'linkedin',
             'reddit', 'lastfm', 'flickr', 'foursquare', 'pandora', 'goodreads',
             'multiply', 'github', 'redbubble'})
        self.assertEqual(
            set(InstantMessenger.objects.values_list('slug', flat=True)),
            {'aim', 'gtalk', 'msn', 'skype', 'y'})


class ReSeedingAnExistingDatabaseTests(TestCase):
    """The migration has to be safe on a database the receiver already filled."""

    def test_running_again_creates_no_duplicates(self):
        seed.seed_networks(global_apps, None)

        self.assertEqual(SocialNetwork.objects.count(), 15)
        self.assertEqual(InstantMessenger.objects.count(), 5)

    def test_the_unused_networks_are_removed(self):
        _recreate_retired()

        seed.seed_networks(global_apps, None)

        self.assertEqual(SocialNetwork.objects.count(), 15)
        self.assertFalse(
            SocialNetwork.objects.filter(slug='pownce').exists())

    def test_a_retired_network_someone_is_using_is_kept(self):
        _recreate_retired()
        user = User.objects.create_user('holdout', 'holdout@example.com', 'pw')
        SocialNetworkProfile.objects.create(user=user, network_id='pownce',
                                            username='ancient')

        seed.seed_networks(global_apps, None)

        self.assertTrue(SocialNetwork.objects.filter(slug='pownce').exists())
        self.assertEqual(
            SocialNetworkProfile.objects.get(network_id='pownce').name,
            'Pownce')

    def test_a_rescued_network_is_reported_with_the_icon_to_restore(self):
        # The icon files for retired networks are gone, and a missing static
        # file is a 500 under ManifestStaticFilesStorage rather than a broken
        # image. Whoever runs the cutover has to be told which one to restore.
        _recreate_retired()
        user = User.objects.create_user('latecomer', 'late@example.com', 'pw')
        SocialNetworkProfile.objects.create(user=user, network_id='pownce',
                                            username='ancient')

        old_disable = logging.getLogger().manager.disable
        logging.disable(logging.NOTSET)
        self.addCleanup(logging.disable, old_disable)

        with self.assertLogs(seed.__name__, level='WARNING') as logged:
            seed.seed_networks(global_apps, None)

        self.assertEqual(len(logged.output), 1)
        self.assertIn('pownce', logged.output[0])
        self.assertIn('pownce.png', logged.output[0])

    def test_nothing_is_reported_when_nothing_needed_rescuing(self):
        _recreate_retired()

        old_disable = logging.getLogger().manager.disable
        logging.disable(logging.NOTSET)
        self.addCleanup(logging.disable, old_disable)

        with self.assertNoLogs(seed.__name__, level='WARNING'):
            seed.seed_networks(global_apps, None)

    def test_reversing_restores_the_previous_urls(self):
        seed.restore_urls(global_apps, None)

        urls = dict(SocialNetwork.objects.values_list('slug', 'url'))
        self.assertEqual(urls['twitter'], 'http://twitter.com/%s')
        self.assertEqual(urls['pandora'], 'http://pandora.com/people/%s')

    def test_an_unused_messenger_is_removed(self):
        InstantMessenger.objects.create(slug='icq', name='ICQ',
                                        url='http://www.icq.com/people/%s',
                                        identifier='', icon='icq.png')

        seed.seed_networks(global_apps, None)

        self.assertEqual(InstantMessenger.objects.count(), 5)
        self.assertFalse(InstantMessenger.objects.filter(slug='icq').exists())

    def test_a_messenger_someone_is_using_is_kept(self):
        InstantMessenger.objects.create(slug='icq', name='ICQ',
                                        url='http://www.icq.com/people/%s',
                                        identifier='', icon='icq.png')
        user = User.objects.create_user('chatter', 'chatter@example.com', 'pw')
        InstantMessengerProfile.objects.create(user=user, network_id='icq',
                                               username='123456')

        seed.seed_networks(global_apps, None)

        self.assertTrue(InstantMessenger.objects.filter(slug='icq').exists())
        self.assertEqual(
            InstantMessengerProfile.objects.get(network_id='icq').name, 'ICQ')

    def test_reversing_deletes_nothing(self):
        user = User.objects.create_user('reverser', 'reverser@example.com', 'pw')
        SocialNetworkProfile.objects.create(user=user, network_id='facebook',
                                            username='42')

        seed.restore_urls(global_apps, None)

        self.assertEqual(SocialNetwork.objects.count(), 15)
        self.assertEqual(InstantMessenger.objects.count(), 5)
        self.assertTrue(SocialNetwork.objects.filter(slug='facebook').exists())
