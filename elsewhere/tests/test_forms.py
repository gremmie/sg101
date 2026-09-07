"""
Tests for the network choice fields.

The choices are built from the database every time a form is constructed, so
what a member can pick follows the seeded rows rather than anything frozen at
import time.
"""
from django.core.cache import cache
from django.test import TestCase

from elsewhere.models import IM_CACHE_KEY
from elsewhere.models import SN_CACHE_KEY
from elsewhere.models import SocialNetwork
from elsewhere.models import SocialNetworkForm


class SocialNetworkFormTests(TestCase):

    def setUp(self):
        cache.delete(SN_CACHE_KEY)
        cache.delete(IM_CACHE_KEY)
        self.addCleanup(cache.delete, SN_CACHE_KEY)
        self.addCleanup(cache.delete, IM_CACHE_KEY)

    def test_the_choices_are_the_seeded_networks(self):
        choices = SocialNetworkForm().fields['network_id'].choices

        self.assertEqual(choices[0][0], '')
        self.assertEqual(len(choices), SocialNetwork.objects.count() + 1)
        self.assertIn(('facebook', 'Facebook'), choices)

    def test_a_retired_network_is_not_offered(self):
        self.assertNotIn(
            'catster', [value for value, label in
                        SocialNetworkForm().fields['network_id'].choices])

    def test_the_choices_are_ordered_by_name(self):
        # Created last so it sorts first. Without an explicit ordering the
        # database hands rows back in insertion order, which for the seeded
        # list alone is alphabetical already and would prove nothing.
        SocialNetwork.objects.create(name='Aardvark', slug='aardvark',
                                     url='https://aardvark.example.com/%s',
                                     identifier='Username', icon='')

        labels = [label for value, label in
                  SocialNetworkForm().fields['network_id'].choices[1:]]

        self.assertEqual(labels[0], 'Aardvark')
        self.assertEqual(labels, sorted(labels, key=str.lower))

    def test_a_network_added_later_is_offered_at_once(self):
        # The managers memoized this dict for the life of the process, so a new
        # network went unoffered until a restart however often the cache
        # expired.
        SocialNetworkForm()

        SocialNetwork.objects.create(name='Newcomer', slug='newcomer',
                                     url='https://new.example.com/%s',
                                     identifier='Username', icon='')

        self.assertIn(('newcomer', 'Newcomer'),
                      SocialNetworkForm().fields['network_id'].choices)
