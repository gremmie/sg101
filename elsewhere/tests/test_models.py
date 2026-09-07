"""
Tests for elsewhere.models -- the stored slug that identifies a network, and
what a profile row does when its slug resolves to nothing.

The slug is the load-bearing part. Profiles store it in a plain CharField with
no referential integrity, so the only thing standing between a member's
profile page and a KeyError is that the network's key never moves.
"""
import logging

from django.contrib.auth.models import User
from django.core.cache import cache
from django.db import IntegrityError, transaction
from django.template import Context, Template
from django.test import TestCase

from elsewhere.models import IM_CACHE_KEY
from elsewhere.models import SN_CACHE_KEY
from elsewhere.models import InstantMessenger
from elsewhere.models import InstantMessengerProfile
from elsewhere.models import SocialNetwork
from elsewhere.models import SocialNetworkProfile
from elsewhere.models import get_instant_messanger_data
from elsewhere.models import get_social_network_data


def _clear_network_caches():
    """Drop both the cache entries and the managers' in-process memo."""
    cache.delete(SN_CACHE_KEY)
    cache.delete(IM_CACHE_KEY)


class NetworkSlugTests(TestCase):

    def setUp(self):
        _clear_network_caches()
        self.addCleanup(_clear_network_caches)

    def test_lookup_is_keyed_on_the_stored_slug(self):
        SocialNetwork.objects.create(name='Example Net', slug='exnet',
                                     url='https://example.com/%s',
                                     identifier='Username', icon='exnet.png')

        data = get_social_network_data()

        self.assertIn('exnet', data)
        self.assertEqual(data['exnet']['name'], 'Example Net')
        # slugify('Example Net') would be 'example-net' -- the stored slug is
        # what identifies the network, not anything derived from the name.
        self.assertNotIn('example-net', data)

    def test_renaming_a_network_does_not_move_its_slug(self):
        net = SocialNetwork.objects.create(name='Example Net', slug='exnet',
                                           url='https://example.com/%s',
                                           identifier='Username',
                                           icon='exnet.png')
        user = User.objects.create_user('renamer', 'renamer@example.com', 'pw')
        profile = SocialNetworkProfile.objects.create(user=user,
                                                      network_id='exnet',
                                                      username='bob')

        net.name = 'Example Net Reloaded'
        net.save()
        _clear_network_caches()

        self.assertEqual(SocialNetwork.objects.get(pk=net.pk).slug, 'exnet')
        self.assertEqual(profile.name, 'Example Net Reloaded')
        self.assertEqual(profile.url, 'https://example.com/bob')

    def test_two_networks_cannot_share_a_slug(self):
        SocialNetwork.objects.create(name='First', slug='dupe',
                                     url='https://one.example.com/%s',
                                     identifier='Username', icon='')

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                SocialNetwork.objects.create(name='Second', slug='dupe',
                                             url='https://two.example.com/%s',
                                             identifier='Username', icon='')

    def test_instant_messengers_are_keyed_on_their_slug_too(self):
        InstantMessenger.objects.create(name='Example IM', slug='exim',
                                        url='exim:chat?id=%s',
                                        identifier='', icon='exim.png')

        data = get_instant_messanger_data()

        self.assertIn('exim', data)
        self.assertEqual(data['exim']['name'], 'Example IM')

    def test_saving_a_network_busts_its_cached_data(self):
        get_social_network_data()
        self.assertIsNotNone(cache.get(SN_CACHE_KEY))

        SocialNetwork.objects.create(name='Latecomer', slug='late',
                                     url='https://late.example.com/%s',
                                     identifier='Username', icon='')

        self.assertIn('late', get_social_network_data())


class UnresolvableNetworkIdTests(TestCase):
    """A profile row whose slug names no network must not take the page down."""

    def setUp(self):
        _clear_network_caches()
        self.addCleanup(_clear_network_caches)
        self.user = User.objects.create_user('orphan', 'orphan@example.com',
                                             'pw')
        SocialNetwork.objects.create(name='Good Net', slug='goodnet',
                                     url='https://good.example.com/%s',
                                     identifier='Username', icon='good.png')
        self.good = SocialNetworkProfile.objects.create(
            user=self.user, network_id='goodnet', username='alice')
        self.orphan = SocialNetworkProfile.objects.create(
            user=self.user, network_id='no-such-net', username='bob')

    def test_data_item_is_none_rather_than_a_key_error(self):
        self.assertIsNone(self.orphan.data_item)

    def test_the_display_attributes_are_empty(self):
        self.assertEqual(self.orphan.name, '')
        self.assertEqual(self.orphan.url, '')
        self.assertEqual(self.orphan.icon_name, '')

    def test_the_entry_is_skipped_and_the_rest_of_the_page_renders(self):
        template = Template(
            '{% load elsewhere_tags %}{% elsewhere_links user %}')

        html = template.render(Context({'user': self.user}))

        self.assertIn('Good Net', html)
        self.assertNotIn('no-such-net', html)
        self.assertNotIn('href=""', html)

    def test_an_unresolvable_slug_is_logged(self):
        old_disable = logging.getLogger().manager.disable
        logging.disable(logging.NOTSET)
        self.addCleanup(logging.disable, old_disable)

        with self.assertLogs('elsewhere.models', level='WARNING') as logged:
            self.orphan.data_item

        self.assertIn('no-such-net', logged.output[0])

    def test_an_instant_messenger_row_is_guarded_the_same_way(self):
        orphan_im = InstantMessengerProfile.objects.create(
            user=self.user, network_id='no-such-im', username='bob')

        self.assertIsNone(orphan_im.data_item)
        self.assertEqual(orphan_im.name, '')
