"""
Tests for the potd management command.

``pick_potd`` is run on a schedule (celery beat / cron) to advance the Photo of
the Day. The underlying tool and celery task are covered in test_tools.py /
test_tasks.py; this covers the ``manage.py pick_potd`` command wrapper itself so
the invocation path can't regress silently.
"""
from django.core.management import call_command
from django.test import TestCase

from potd.models import Current


class PickPotdCommandTests(TestCase):
    fixtures = ['potd_test.json']

    def test_command_advances_the_current_photo(self):
        call_command('pick_potd')
        self.assertEqual(Current.objects.get(pk=1).potd.pk, 2)
