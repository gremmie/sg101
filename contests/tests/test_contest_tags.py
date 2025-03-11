"""
Tests for the contests application's template tags.

"""
from django.template import Context, Template
from django.test import TestCase

from datetime import datetime, timedelta

from contests.models import Contest
from contests.templatetags.contest_tags import latest_contests_block


class ContestsTemplateTagsTestCase(TestCase):
    def setUp(self):
        now = datetime.now()
        then = now - timedelta(days=3)
        end = now + timedelta(days=30)
        contests = [
            Contest(title='Active Contest', is_public=True,
                    creation_date=then, end_date=end, slug='active'),
            Contest(title='Non-public Contest', is_public=False,
                    creation_date=then, end_date=end, slug='secret'),
            Contest(title='Past Contest', is_public=True,
                    creation_date=then, win_date=now, end_date=end,
                    slug='past'),
        ]
        for contest in contests:
            contest.save()

        self.template_string = ('{% load contest_tags %}'
            '{% latest_contests_block %}')

    def render_template(self, context_dict=None):
        template = Template(self.template_string)
        context = Context(context_dict)
        return template.render(context)

    def test_latest_contests_block(self):
        rendered = self.render_template()

        self.assertIn('Active Contest', rendered)
        self.assertNotIn('Non-public Contest', rendered)
        self.assertNotIn('Past Contest', rendered)

    def test_latest_contests_block_v3(self):
        rendered = self.render_template({'V3_DESIGN': True})

        self.assertIn('Active Contest', rendered)
        self.assertNotIn('Non-public Contest', rendered)
        self.assertNotIn('Past Contest', rendered)

    def test_latest_contests_block_with_no_contests(self):
        Contest.objects.all().delete()
        rendered = self.render_template({'V3_DESIGN': True})

        self.assertNotIn('Active Contest', rendered)
        self.assertNotIn('Non-public Contest', rendered)
        self.assertNotIn('Past Contest', rendered)
        self.assertIn('No contests at this time', rendered)
