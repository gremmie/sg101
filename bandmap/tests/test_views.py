"""
Unit tests for the bandmap application views.

"""
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
        """TODO"""
