"""
Unit tests for the bulletin app template tags.

"""
from datetime import timedelta

from django.template import Context, Template
from django.test import TestCase
from django.utils import timezone

from bulletins.models import Bulletin


class BulletinTemplatetagsTestCase(TestCase):

    TEMPLATE = Template('{% load bulletin_tags %} {% current_bulletins %}')

    def setUp(self):
        now = timezone.now()
        bulletins = [
            Bulletin(title='All Points', text='No end date',
                     start_date=now - timedelta(days=3)),
            Bulletin(title='Attention', text='Has end date within window',
                     start_date=now - timedelta(days=30),
                     end_date=now + timedelta(days=30)),
            Bulletin(title='Expired', text='Ended already',
                     start_date=now - timedelta(days=30),
                     end_date=now - timedelta(days=10)),
            Bulletin(title='Not enabled', text='Not enabled text',
                     start_date=now - timedelta(days=30),
                     is_enabled=False)
        ]
        for bulletin in bulletins:
            bulletin.save()

    def test_renders_expected_bulletins(self):
        rendered = self.TEMPLATE.render(Context({}))

        self.assertIn('All Points', rendered)
        self.assertIn('No end date', rendered)
        self.assertIn('Attention', rendered)
        self.assertIn('Has end date within window', rendered)

        self.assertNotIn('Expired', rendered)
        self.assertNotIn('Ended already', rendered)
        self.assertNotIn('Not enabled', rendered)

