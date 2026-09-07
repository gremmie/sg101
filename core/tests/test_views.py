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
        # Alphabetical, not the order they were created in -- which is what
        # this used to assert, and what no engine ever promised.
        response = self.client.get(self.url, {'q': 'ab'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), ['abdel', 'abdul', 'abe'])

    def test_the_limit_takes_the_alphabetically_first_matches(self):
        # The defect this ordering fixes. A prefix can match hundreds of
        # members, so which few a LIMIT returns has to be decided by something
        # rather than left to the query plan.
        for name in ['abner', 'abbot', 'abacus']:
            User.objects.create_user(name, '', 'pw')

        response = self.client.get(self.url, {'q': 'ab', 'limit': 3})
        self.assertEqual(response.json(), ['abacus', 'abbot', 'abdel'])

    def test_inactive_users_are_still_excluded(self):
        User.objects.create_user('abzz', '', 'pw')
        User.objects.filter(username='abzz').update(is_active=False)
        response = self.client.get(self.url, {'q': 'ab'})
        self.assertNotIn('abzz', response.json())

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

    def test_colophon_does_not_credit_django_tagging(self):
        """It is a live page, and the credit linked to a Google Code URL that
        has been dead for years."""
        body = self.client.get(reverse('colophon')).content.decode()

        self.assertNotIn('django-tagging', body)
        self.assertNotIn('code.google.com/p/django-tagging', body)

    def test_colophon_library_list_is_not_left_mispunctuated(self):
        """Removing an item from a comma-joined list is how a stray comma or a
        doubled space ships to a live page."""
        body = self.client.get(reverse('colophon')).content.decode()

        self.assertNotIn(', ,', body)
        self.assertNotIn(',,', body)
        self.assertNotIn('  ', body.split('<p>The following 3rd party')[1]
                         .split('</p>')[0])

    def test_privacy_view(self):
        response = self.client.get(reverse('privacy'))
        self.assertEqual(response.status_code, 200)

    def test_tos_view(self):
        response = self.client.get(reverse('tos'))
        self.assertEqual(response.status_code, 200)
