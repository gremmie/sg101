"""Tests for project-level URL wiring in sg101/urls.py."""
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse


class AdminPasswordResetTests(TestCase):
    """The admin login page renders a "Forgotten your password?" link only when
    'admin_password_reset' reverses, so that name has to keep resolving. It
    points at the site's own reset flow; the parallel admin one it used to run
    was unreachable (its companion routes were never named) and its confirm URL
    still expected the pre-1.6 uidb36 format.

    """
    def test_admin_password_reset_redirects_to_the_site_flow(self):
        response = self.client.get(reverse('admin_password_reset'))

        self.assertRedirects(response, reverse('accounts-password_reset'))

    def test_admin_login_page_offers_the_reset_link(self):
        response = self.client.get(reverse('admin:login'))

        self.assertContains(response, reverse('admin_password_reset'))

    def test_retired_reset_routes_are_gone(self):
        # Log in as staff: the admin's catch-all view (Django 3.2+) redirects
        # anonymous users to the login page for any unknown /admin/ path, so an
        # unauthenticated request can't tell a retired route from a missing one.
        # For an authenticated staff user the catch-all raises the real 404.
        User.objects.create_superuser('admin', 'admin@example.com', 'pw')
        self.client.login(username='admin', password='pw')

        for path in ['/admin/password_reset/done/',
                     '/reset/MQ-5lo-ec3ad4f6d9b6f0b1a2c3/',
                     '/reset/done/']:
            self.assertEqual(self.client.get(path).status_code, 404,
                             msg='%s should no longer resolve' % path)
