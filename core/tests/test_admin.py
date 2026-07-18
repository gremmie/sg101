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
from django.core.urlresolvers import reverse
from django.test import TestCase


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
