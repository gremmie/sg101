"""
Unit tests for the core app views.

"""
from django.contrib.auth.models import User
from django.urls import reverse
from django.test import TestCase


class MarkdownHelpTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('pjmoto', '', 'pw')
        self.user.save()
        self.client.login(username='pjmoto', password='pw')
        self.url = reverse('core-markdown_help')

    def test_happy_path(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_unauthenticated_case(self):
        self.client.logout()
        response = self.client.get(self.url, follow=True)
        self.assertEqual(response.redirect_chain,
            [('/accounts/login/?next=/core/markdown_help/', 302)])


class AjaxUsersTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('pjmoto', '', 'pw')
        self.user.save()
        self.client.login(username='pjmoto', password='pw')
        self.url = reverse('core-ajax_users')

        User.objects.create_user('abe', '', 'pw')
        User.objects.create_user('abdul', '', 'pw')
        User.objects.create_user('abdel', '', 'pw')

    def test_happy_path(self):
        response = self.client.get(self.url, {'q': 'ab'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), ['abe', 'abdul', 'abdel'])

    def test_unauthenticated_case(self):
        self.client.logout()
        response = self.client.get(self.url, {'q': 'ab'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])


class FixedViewsTestCase(TestCase):
    def test_about_view(self):
        response = self.client.get(reverse('about'))
        self.assertEqual(response.status_code, 200)

    def test_colophon_view(self):
        response = self.client.get(reverse('colophon'))
        self.assertEqual(response.status_code, 200)

    def test_privacy_view(self):
        response = self.client.get(reverse('privacy'))
        self.assertEqual(response.status_code, 200)

    def test_tos_view(self):
        response = self.client.get(reverse('tos'))
        self.assertEqual(response.status_code, 200)
