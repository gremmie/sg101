"""
Unit tests for the bandmap application views.

"""
import datetime

from django.test import TestCase
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User

from bandmap.models import BandEntry


class NotLoggedInTestCase(TestCase):
    """Tests for a non-authenticated user.

    """
    LOGIN_URL = reverse('accounts-login')

    def test_map(self):
        url = reverse('bandmap-map')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_get_add(self):
        url = reverse('bandmap-add')
        response = self.client.get(url, follow=True)
        self.assertRedirects(response, self.LOGIN_URL + '?next=' + url)

    def test_post_add(self):
        url = reverse('bandmap-add')
        response = self.client.post(url, follow=True)
        self.assertRedirects(response, self.LOGIN_URL + '?next=' + url)


class BasicTestCase(TestCase):
    """Tests for an authenticated user."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='pj', email='pj@example.com', password='top_secret')
        self.client.login(username='pj', password='top_secret')

    def test_map(self):
        url = reverse('bandmap-map')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_get_add(self):
        url = reverse('bandmap-add')
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)

    def test_post_add(self):
        url = reverse('bandmap-add')
        post_data = {
            'name': 'Test Band',
            'url': 'http://example.com/',
            'location': 'Here & There',
            'note': 'They suck',
            'is_active': 'on',
            'lat': '42.0',
            'lon': '-23.5',
        }
        now = datetime.datetime.now()
        delta_t = datetime.timedelta(seconds=1)
        response = self.client.post(url, data=post_data, follow=True)
        self.assertRedirects(response, url)

        self.assertEqual(BandEntry.objects.all().count(), 1)
        entry = BandEntry.objects.get(pk=1)
        self.assertEqual(entry.name, post_data['name'])
        self.assertEqual(entry.user, self.user)
        self.assertEqual(entry.user, self.user)
        self.assertTrue(now - entry.date_submitted < delta_t)
        self.assertIsNone(entry.date_approved)
        self.assertEqual(entry.url, post_data['url'])
        self.assertEqual(entry.location, post_data['location'])
        self.assertAlmostEqual(entry.lat, float(post_data['lat']))
        self.assertAlmostEqual(entry.lon, float(post_data['lon']))
        self.assertEqual(entry.note, post_data['note'])
        self.assertTrue(entry.is_active)
        self.assertFalse(entry.is_approved)
