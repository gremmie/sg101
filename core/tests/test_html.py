"""Tests for the core.html module."""
import unittest

from unittest.mock import call, patch

from core.html import clean_html, _CLEAN_PROFILES
from core.html import ImageCheckError
from core.html import image_check


TEST_HTML = """
<p>Posters and Facebook events are starting to come in...</p>
<p><img src="{src1}" alt="image"></p>
<p><img src="{src2}" alt="image"></p>
"""


class ImageCheckTestCase(unittest.TestCase):
    def setUp(self):
        self.allowed_hosts = ['example.com']

    def test_happy_path(self):
        url1 = 'https://example.com/1.jpg'
        url2 = 'https://example.com/2.jpg'
        html = TEST_HTML.format(src1=url1, src2=url2)

        result = image_check(html, self.allowed_hosts)
        self.assertTrue(result)

    def test_empty_image(self):
        url1 = 'https://example.com/1.jpg'
        url2 = ''
        html = TEST_HTML.format(src1=url1, src2=url2)

        self.assertRaises(ImageCheckError, image_check, html, self.allowed_hosts)

    def test_relative_ok(self):
        url1 = 'https://example.com/1.jpg'
        url2 = '/some/path/2.jpg'
        html = TEST_HTML.format(src1=url1, src2=url2)

        result = image_check(html, self.allowed_hosts)
        self.assertTrue(result)

    def test_non_https(self):
        url1 = 'http://example.com/1.jpg'
        url2 = 'https://example.com/2.jpg'
        html = TEST_HTML.format(src1=url1, src2=url2)

        self.assertRaises(ImageCheckError, image_check, html, self.allowed_hosts)

    def test_missing_hostname(self):
        url1 = 'http:///1.jpg'
        url2 = 'https://example.com/2.jpg'
        html = TEST_HTML.format(src1=url1, src2=url2)

        self.assertRaises(ImageCheckError, image_check, html, self.allowed_hosts)

    def test_hostname_not_allowed1(self):
        url1 = 'https://xxx.example.com/1.jpg'
        url2 = 'https://example.com/2.jpg'
        html = TEST_HTML.format(src1=url1, src2=url2)

        self.assertRaises(ImageCheckError, image_check, html, self.allowed_hosts)

    def test_hostname_not_allowed2(self):
        url1 = 'https://xxx.example.com/1.jpg'
        url2 = 'https://yyy.example.com/2.jpg'
        html = TEST_HTML.format(src1=url1, src2=url2)

        self.assertRaises(ImageCheckError, image_check, html, self.allowed_hosts)

    def test_empty_string(self):
        result = image_check('')
        self.assertTrue(result)

    def test_whitespace(self):
        result = image_check('\r\n\r\n')
        self.assertTrue(result)


class CleanHtmlTestCase(unittest.TestCase):
    def test_all_whitespace(self):
        text = '  \t   \n  '
        result = clean_html(text)
        self.assertEqual(result, '')

    @patch('core.html.bleach.clean')
    def test_comments(self, clean_mock):
        text = ' Lorem ipsum '
        result = clean_html(text)
        self.assertEqual(clean_mock.mock_calls, [
            call('Lorem ipsum', tags=_CLEAN_PROFILES['comments'][0],
                 attributes=_CLEAN_PROFILES['comments'][1], strip=True,
                 strip_comments=True),
        ])

    @patch('core.html.bleach.clean')
    def test_news(self, clean_mock):
        text = ' Lorem ipsum '
        result = clean_html(text, profile='news')
        self.assertEqual(clean_mock.mock_calls, [
            call('Lorem ipsum', tags=_CLEAN_PROFILES['news'][0],
                 attributes=_CLEAN_PROFILES['news'][1], strip=True,
                 strip_comments=True),
        ])

    def test_strips_disallowed_tags(self):
        # strip=True drops the tag and keeps its text, which lands in the
        # output as inert content rather than as script.
        self.assertEqual(clean_html('<script>alert(1)</script>hi'),
                         'alert(1)hi')

    def test_strips_style_attribute(self):
        # Neither profile allows style=, and there is no styles= kwarg any more
        # telling bleach which declarations to keep. Inline CSS goes.
        self.assertEqual(clean_html('<p style="color:red">x</p>'),
                         '<p>x</p>')

    def test_strips_event_handler(self):
        self.assertEqual(
            clean_html('<img src="https://example.com/a.png" onerror="alert(1)">'),
            '<img src="https://example.com/a.png">')
