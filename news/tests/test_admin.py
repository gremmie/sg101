"""Tests for the news admin."""
import re

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse


def textarea_classes(html):
    """Each textarea's name, mapped to its list of classes."""
    found = {}
    for tag in re.findall(r'<textarea[^>]*>', html):
        attrs = dict(re.findall(r'(\w+)="([^"]*)"', tag))
        found[attrs['name']] = attrs.get('class', '').split()
    return found


class RichTextEditorTests(TestCase):
    """
    Which textareas TinyMCE turns into rich-text editors.

    The Markdown fields and the meta description are plain text, so they carry
    the class TinyMCE's init skips. It has to be in the served HTML: TinyMCE
    converts textareas as the document finishes parsing, before any jQuery
    ready handler could add it.

    """
    PLAIN = {'short_markup', 'long_markup', 'meta_description'}
    RICH = {'short_text', 'long_text', 'admin_content'}

    def setUp(self):
        User.objects.create_superuser('admin', 'admin@example.com', 'pw')
        self.assertTrue(self.client.login(username='admin', password='pw'))

    def _textarea_classes(self, url):
        html = self.client.get(url).content.decode('utf-8')
        return textarea_classes(html)

    def _assert_editors(self, url):
        classes = self._textarea_classes(url)
        self.assertEqual(set(classes), self.PLAIN | self.RICH)
        for name in self.PLAIN:
            self.assertIn('mceNoEditor', classes[name], name)
        for name in self.RICH:
            self.assertNotIn('mceNoEditor', classes[name], name)
            # Still styled as the admin's own wide textarea.
            self.assertIn('vLargeTextField', classes[name], name)

    def test_story(self):
        self._assert_editors(reverse('admin:news_story_add'))

    def test_pending_story(self):
        self._assert_editors(reverse('admin:news_pendingstory_add'))
