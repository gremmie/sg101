"""
Unit tests for the antispam application views.

"""
from django.test import TestCase
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User


class SuspendedViewTestCase(TestCase):
    def setUp(self):
        self.url = reverse('antispam-suspended')

    def test_suspended_user_is_active(self):
        self.user = User.objects.create_user(
            username='pj', email='pj@example.com', password='top_secret')
        self.client.login(username='pj', password='top_secret')
        self.assertTrue(self.user.is_active)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_suspended_user_is_not_active(self):
        url = reverse('antispam-suspended')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
