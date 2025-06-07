"""
Tests for the core markup module.

"""
import textwrap
import unittest

from django.test import TestCase

from core.markup import Markdown, markdown, SiteMarkup, site_markup


class MarkdownTestCase(unittest.TestCase):

    TEST_TEXT = textwrap.dedent("""\
        Some text.
        https://example.com
        ---deleted text---
        """)

    EXPECTED = textwrap.dedent(u"""\
        <p>Some text.<br>
        <a href="https://example.com">https://example.com</a><br>
        <del>deleted text</del></p>""")

    def test_markdown_class(self):
        md = Markdown()
        output = md.convert(self.TEST_TEXT)
        self.assertEqual(output, self.EXPECTED)

    def test_markdown_function(self):
        output = markdown(self.TEST_TEXT)
        self.assertEqual(output, self.EXPECTED)


class SiteMarkdupTestCase(TestCase):
    fixtures = ['smilies.json']

    TEST_TEXT = textwrap.dedent("""\
        Some text.
        https://example.com
        ---deleted text---
        :sg101:
        """)

    EXPECTED = textwrap.dedent(u"""\
        <p>Some text.<br>
        <a href="https://example.com">https://example.com</a><br>
        <del>deleted text</del><br>
        <img src="/media/smiley/images/icon_sg101.gif" alt="SG101!" title="SG101!"></p>""")

    def test_site_markup_class(self):
        sm = SiteMarkup()
        output = sm.convert(self.TEST_TEXT)
        self.assertEqual(output, self.EXPECTED)

    def test_site_markup_function(self):
        output = site_markup(self.TEST_TEXT)
        self.assertEqual(output, self.EXPECTED)
