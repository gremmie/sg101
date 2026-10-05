"""Tests for the contests admin."""
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
    """The meta description is plain text; the description is rich text."""

    def setUp(self):
        User.objects.create_superuser('admin', 'admin@example.com', 'pw')
        self.assertTrue(self.client.login(username='admin', password='pw'))

    def test_only_the_meta_description_is_left_plain(self):
        html = self.client.get(
            reverse('admin:contests_contest_add')).content.decode('utf-8')
        classes = textarea_classes(html)

        self.assertIn('mceNoEditor', classes['meta_description'])
        self.assertNotIn('mceNoEditor', classes['description'])
