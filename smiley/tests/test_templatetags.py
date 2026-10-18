"""Tests for the smiley app's template tags."""
import re

from django.core.cache import cache
from django.template import Context, Template
from django.test import TestCase

from smiley.models import Smiley


DATA_CODE = re.compile(r'data-code="([^"]*)"')


class SmileyPickerTestCase(TestCase):
    """{% smiley_picker %} renders every smiley as a button, main set first."""
    fixtures = ['smilies.json']

    def setUp(self):
        # get_smilies caches each set for an hour, and the test cache outlives
        # a test, so a set cached by an earlier test would render instead.
        cache.clear()
        self.addCleanup(cache.clear)

    def render(self):
        template = Template('{% load smiley_tags %}{% smiley_picker %}')
        return template.render(Context({}))

    def test_main_smileys_come_before_the_extras(self):
        # Nothing makes codes unique (:lol: was once both a main and an extra
        # smiley), so this compares the whole sequence rather than classifying
        # each code.
        main = Smiley.objects.filter(is_extra=False)
        extra = Smiley.objects.filter(is_extra=True)
        self.assertTrue(main and extra)
        expected = [s.code for s in main] + [s.code for s in extra]
        self.assertEqual(DATA_CODE.findall(self.render()), expected)

    def test_every_smiley_has_one_button(self):
        codes = DATA_CODE.findall(self.render())
        self.assertEqual(sorted(codes), sorted(Smiley.objects.values_list('code', flat=True)))

    def test_images_are_lazy_and_have_alt_text(self):
        images = re.findall(r'<img [^>]*>', self.render())
        self.assertEqual(len(images), Smiley.objects.count())
        for image in images:
            self.assertIn('loading="lazy"', image)
            self.assertRegex(image, r'alt="[^"]+"')

    def test_codes_are_escaped_in_the_attribute(self):
        # No real code holds these characters; one that did would end the
        # attribute early without escaping.
        Smiley.objects.create(code=':"<&:', title='Test', image='smiley/images/test.gif')
        self.assertIn('data-code=":&quot;&lt;&amp;:"', self.render())

    def test_the_extras_are_headed_more_smileys(self):
        rendered = self.render()
        main = Smiley.objects.filter(is_extra=False)
        extra = Smiley.objects.filter(is_extra=True)
        heading = rendered.index('More smileys')
        self.assertLess(rendered.rindex('data-code="{}"'.format(main.last().code)), heading)
        self.assertGreater(rendered.index('data-code="{}"'.format(extra.first().code)), heading)
