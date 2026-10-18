"""Tests for the smiley models."""
from django.core.cache import cache
from django.test import TestCase

from smiley.models import Smiley


class SmileyCacheTestCase(TestCase):
    """Each cached view of the smileys shows an edit made after it was cached."""
    fixtures = ['smilies.json']

    def setUp(self):
        cache.clear()
        self.addCleanup(cache.clear)

    def change_code(self, is_extra):
        smiley = Smiley.objects.filter(is_extra=is_extra).first()
        smiley.code = ':changed:'
        smiley.save()

    def test_smiley_map(self):
        Smiley.objects.get_smiley_map()
        self.change_code(False)
        self.assertIn(':changed:', Smiley.objects.get_smiley_map())

    def test_main_smileys(self):
        list(Smiley.objects.get_smilies())
        self.change_code(False)
        self.assertIn(':changed:', [s.code for s in Smiley.objects.get_smilies()])

    def test_extra_smileys(self):
        list(Smiley.objects.get_smilies(extra=True))
        self.change_code(True)
        self.assertIn(':changed:', [s.code for s in Smiley.objects.get_smilies(extra=True)])

    def test_regexes_with_relative_urls(self):
        Smiley.objects.get_smiley_regexes(relative_urls=True)
        self.change_code(False)
        regexes = Smiley.objects.get_smiley_regexes(relative_urls=True)
        self.assertTrue(any(regex.search('a :changed: b') for regex, _ in regexes))

    def test_regexes_with_absolute_urls(self):
        Smiley.objects.get_smiley_regexes(relative_urls=False)
        self.change_code(False)
        regexes = Smiley.objects.get_smiley_regexes(relative_urls=False)
        self.assertTrue(any(regex.search('a :changed: b') for regex, _ in regexes))

    def test_a_deleted_smiley_is_gone(self):
        smiley = Smiley.objects.filter(is_extra=False).first()
        pk = smiley.pk      # delete() sets smiley.pk to None
        list(Smiley.objects.get_smilies())
        smiley.delete()
        self.assertNotIn(pk, [s.pk for s in Smiley.objects.get_smilies()])
