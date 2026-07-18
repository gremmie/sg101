"""
Unit tests for the bandmap application views.

"""
import datetime
import json

from django.test import TestCase
from django.urls import reverse
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

class QueryTestCase(TestCase):
    """Testing the query view function which returns JSON."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='pj', email='pj@example.com', password='top_secret')

        now = datetime.datetime.now()

        kwargs = {
            'name': 'Test Band 1',
            'user': self.user,
            'date_submitted': now,
            'date_approved': now,
            'url': 'http://example.com',
            'location': 'Somewhere',
            'lat': 42.0,
            'lon': -30.0,
            'note': 'Some text here',
            'is_active': True,
            'is_approved': True,
        }
        BandEntry.objects.create(**kwargs)

        kwargs['name'] = 'Test Band 2'
        kwargs['is_active'] = False
        BandEntry.objects.create(**kwargs)

        kwargs['name'] = 'Test Band 3'
        kwargs['is_active'] = True
        kwargs['is_approved'] = False
        BandEntry.objects.create(**kwargs)

    def test_query(self):
        url = reverse('bandmap-query')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        result = json.loads(response.content)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['name'], 'Test Band 1')
        self.assertEqual(result[1]['name'], 'Test Band 2')

    def test_query_all(self):
        url = reverse('bandmap-query')
        response = self.client.get(url, {'show': 'all'})
        self.assertEqual(response.status_code, 200)

        result = json.loads(response.content)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['name'], 'Test Band 1')
        self.assertEqual(result[1]['name'], 'Test Band 2')

    def test_query_active(self):
        url = reverse('bandmap-query')
        response = self.client.get(url, {'show': 'active'})
        self.assertEqual(response.status_code, 200)

        result = json.loads(response.content)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['name'], 'Test Band 1')

    def test_query_inactive(self):
        url = reverse('bandmap-query')
        response = self.client.get(url, {'show': 'inactive'})
        self.assertEqual(response.status_code, 200)

        result = json.loads(response.content)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['name'], 'Test Band 2')
