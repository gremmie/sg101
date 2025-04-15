"""Tests for the core.html module."""
import unittest

from mock import call, patch

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
                 attributes=_CLEAN_PROFILES['comments'][1],
                 styles=_CLEAN_PROFILES['comments'][2], strip=True,
                 strip_comments=True),
        ])

    @patch('core.html.bleach.clean')
    def test_comments(self, clean_mock):
        text = ' Lorem ipsum '
        result = clean_html(text, profile='news')
        self.assertEqual(clean_mock.mock_calls, [
            call('Lorem ipsum', tags=_CLEAN_PROFILES['news'][0],
                 attributes=_CLEAN_PROFILES['news'][1],
                 styles=_CLEAN_PROFILES['news'][2], strip=True,
                 strip_comments=True),
        ])
