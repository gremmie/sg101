"""
Smoke tests for the Django admin.

The admin is a heavily-used staff tool that touches nearly every model, yet it
has almost no direct test coverage. These walk the admin registry and load each
model's changelist (and the admin index) as a superuser, asserting a clean 200.
It is cheap insurance that the admin still boots for every registered model --
the kind of breakage a framework upgrade can introduce silently.
"""
from django.contrib import admin
from django.contrib.auth.models import User
from django.urls import reverse
from django.test import TestCase
from django.utils import timezone

from news.models import Category, PendingStory


class AdminSmokeTests(TestCase):

    def setUp(self):
        User.objects.create_superuser('admin', 'admin@example.com', 'pw')
        self.assertTrue(self.client.login(username='admin', password='pw'))

    def test_admin_index_loads(self):
        response = self.client.get(reverse('admin:index'))
        self.assertEqual(response.status_code, 200)

    def test_every_registered_changelist_loads(self):
        failures = []
        for model in admin.site._registry:
            opts = model._meta
            url = reverse('admin:%s_%s_changelist' % (opts.app_label,
                                                      opts.model_name))
            response = self.client.get(url)
            if response.status_code != 200:
                failures.append('%s.%s -> %d' % (opts.app_label,
                                                 opts.model_name,
                                                 response.status_code))

        self.assertEqual(failures, [],
                         msg='admin changelists did not return 200: %s'
                             % ', '.join(failures))

    def test_every_add_form_loads(self):
        # The add view exercises each ModelAdmin's form construction. Some models
        # legitimately forbid adding (has_add_permission False), which the admin
        # answers with a 403 -- that is a valid, expected outcome, not a failure.
        failures = []
        for model in admin.site._registry:
            opts = model._meta
            url = reverse('admin:%s_%s_add' % (opts.app_label, opts.model_name))
            response = self.client.get(url)
            if response.status_code not in (200, 403):
                failures.append('%s.%s -> %d' % (opts.app_label,
                                                 opts.model_name,
                                                 response.status_code))

        self.assertEqual(failures, [],
                         msg='admin add forms did not load: %s'
                             % ', '.join(failures))


class ModerationDashboardTests(TestCase):
    """
    The dashboard of pending-moderation counts in the admin header.

    It renders through `nav-global`, a block of Django's own admin template,
    and is styled against Django's own header rules -- so it is exactly the
    kind of thing a Django upgrade moves without any test noticing. It did:
    the header became a flex row in 3.2 and the dashboard sat at the far right
    of it, unremarked, for four rungs.

    """
    def setUp(self):
        User.objects.create_superuser('admin', 'admin@example.com', 'pw')
        self.assertTrue(self.client.login(username='admin', password='pw'))

    def _submit_a_story(self):
        author = User.objects.get(username='admin')
        category = Category.objects.create(title='General', slug='general')
        now = timezone.now()
        PendingStory.objects.create(title='Pending', category=category,
                                    submitter=author, short_markup='Body.',
                                    date_submitted=now, update_date=now)

    def test_the_dashboard_gets_its_own_row_in_the_header(self):
        self._submit_a_story()

        html = self.client.get(reverse('admin:index')).content.decode('utf-8')

        # It is in the header, and it is a full-width flex line rather than a
        # third item sharing the row with the branding and the user tools.
        self.assertIn('<div id="dashboard">', html)
        self.assertIn('flex-wrap', html)
        self.assertIn('flex-basis: 100%', html)

    def test_a_pending_item_is_counted_and_linked(self):
        self._submit_a_story()

        html = self.client.get(reverse('admin:index')).content.decode('utf-8')

        self.assertIn('/admin/news/pendingstory/', html)
        self.assertIn('News</a>: 1', html)

    def test_nothing_pending_renders_no_dashboard(self):
        """
        A zero is hidden, which is why an empty header is the normal case.

        Asserting on the rendered element, not the bare id: `#dashboard-list`
        is also a selector in the stylesheet above, and is on every admin page
        whether or not anything is pending.

        """
        html = self.client.get(reverse('admin:index')).content.decode('utf-8')
        self.assertNotIn('<ul id="dashboard-list">', html)
        self.assertNotIn('<div id="dashboard">', html)


class AdminBrandingTests(TestCase):
    """
    The site's `branding` block override, and what Django puts in its own.

    Overriding a block replaces it wholesale, so anything Django later adds to
    its version silently disappears -- 4.2 put the light/dark theme toggle in
    `branding` for anonymous visitors, and the one admin page an anonymous
    visitor reaches is the login form.

    """
    def test_the_login_page_offers_the_theme_toggle(self):
        html = self.client.get(reverse('admin:login')).content.decode('utf-8')

        self.assertIn('SurfGuitar101.com Site Administration', html)
        self.assertIn('theme-toggle', html)

    def test_a_signed_in_page_shows_exactly_one_toggle(self):
        """
        The toggle is inherited from `userlinks` once staff are signed in, so
        the anonymous copy must not double up on it.

        """
        User.objects.create_superuser('admin', 'admin@example.com', 'pw')
        self.assertTrue(self.client.login(username='admin', password='pw'))

        html = self.client.get(reverse('admin:index')).content.decode('utf-8')

        self.assertEqual(html.count('class="theme-toggle"'), 1)
