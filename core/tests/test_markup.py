"""
Tests for the core markup module.

"""
import textwrap
import unittest

from django.core.cache import cache
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


class DelExtensionTestCase(unittest.TestCase):
    """The ---struck--- syntax, and where its pattern sits in the inline pass.

    Nothing raises when an inline pattern is registered at the wrong priority;
    it just stops producing, or starts eating markup that belongs to another
    pattern. These tests pin both edges of the band the priority has to be in.
    """

    def convert(self, text):
        return Markdown().convert(text)

    def test_struck_text(self):
        self.assertEqual(self.convert('plain ---struck--- text'),
                         '<p>plain <del>struck</del> text</p>')

    def test_struck_text_inside_emphasis(self):
        self.assertEqual(self.convert('*emphasis ---struck--- inside*'),
                         '<p><em>emphasis <del>struck</del> inside</em></p>')

    def test_a_single_run_of_hyphens_is_left_alone(self):
        self.assertEqual(self.convert('nothing ---to see here'),
                         '<p>nothing ---to see here</p>')

    def test_hyphens_in_a_url_do_not_strike_it_through(self):
        """The upper edge: above `autolink` this eats the URL and its href."""
        self.assertEqual(
            self.convert('see http://example.com/a---b---c for details'),
            '<p>see <a href="http://example.com/a---b---c">'
            'http://example.com/a---b---c</a> for details</p>')

    def test_hyphens_in_an_explicit_link_do_not_strike_it_through(self):
        self.assertEqual(
            self.convert('[a link](http://example.com/x---y---z)'),
            '<p><a href="http://example.com/x---y---z">a link</a></p>')


class UrlizeExtensionTestCase(unittest.TestCase):
    """Autolinking, which this extension takes over from Markdown's own."""

    def convert(self, text):
        return Markdown().convert(text)

    def test_full_url(self):
        self.assertEqual(self.convert('http://example.com/'),
                         '<p><a href="http://example.com/">http://example.com/</a></p>')

    def test_url_in_a_sentence(self):
        self.assertEqual(self.convert('go to http://example.com'),
                         '<p>go to <a href="http://example.com">http://example.com</a></p>')

    def test_bare_domain_gets_a_scheme(self):
        self.assertEqual(self.convert('example.com'),
                         '<p><a href="http://example.com">example.com</a></p>')

    def test_www_without_a_scheme(self):
        self.assertEqual(self.convert('www.example.us'),
                         '<p><a href="http://www.example.us">www.example.us</a></p>')

    def test_angle_bracketed_url(self):
        self.assertEqual(self.convert('go to <http://example.com> now!'),
                         '<p>go to <a href="http://example.com">http://example.com</a>'
                         ' now!</p>')

    def test_trailing_punctuation_stays_outside_the_link(self):
        self.assertEqual(self.convert('(www.example.us/path/?name=val)'),
                         '<p>(<a href="http://www.example.us/path/?name=val">'
                         'www.example.us/path/?name=val</a>)</p>')

    def test_a_domain_inside_a_word_is_not_a_link(self):
        self.assertEqual(self.convert('del.icio.us'), '<p>del.icio.us</p>')

    def test_an_explicit_link_still_wins(self):
        self.assertEqual(self.convert('[text](http://example.com)'),
                         '<p><a href="http://example.com">text</a></p>')


class ParserStateTestCase(unittest.TestCase):
    """A Markdown parser accumulates state, so a reused one must be reset.

    Reference definitions and stashed raw HTML live on the instance and are not
    cleared by convert(). Without the reset in Markdown.convert(), a label
    defined in one post resolves in the next one rendered by the same object --
    which is content from one page appearing on another.
    """

    DEFINES_A_REFERENCE = '[secret]: http://internal.example.com/private\n\nsome text'
    MENTIONS_THE_LABEL = 'did anyone see [secret][] here?'

    def test_a_reference_does_not_leak_into_the_next_document(self):
        md = Markdown()
        md.convert(self.DEFINES_A_REFERENCE)
        self.assertEqual(md.convert(self.MENTIONS_THE_LABEL),
                         '<p>did anyone see [secret][] here?</p>')

    def test_a_reference_still_resolves_within_one_document(self):
        md = Markdown()
        output = md.convert('see [secret][] here\n\n'
                            '[secret]: http://internal.example.com/private')
        self.assertEqual(output,
                         '<p>see <a href="http://internal.example.com/private">'
                         'secret</a> here</p>')


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
        <img alt="SG101!" src="/media/smiley/images/icon_sg101.gif" title="SG101!"></p>""")

    def test_site_markup_class(self):
        sm = SiteMarkup()
        output = sm.convert(self.TEST_TEXT)
        self.assertEqual(output, self.EXPECTED)

    def test_site_markup_function(self):
        output = site_markup(self.TEST_TEXT)
        self.assertEqual(output, self.EXPECTED)


class SmileyPaddingTestCase(TestCase):
    """The text the post box's smiley picker leaves renders every smiley.

    A code becomes an image only between whitespace or line ends, so the
    picker pads what it inserts. These are the results its browser tests
    expect (news/tests/test_browser.py, SubmitSmileyPickerTestCase).
    """
    fixtures = ['smilies.json']

    PADDED = {
        'ab :-) cd': 1,
        'ab :-) :D cd': 2,
        # One space between two of the same code: the first match takes it,
        # and only the regex's lookbehind lets the second match too.
        'ab :-) :-) cd': 2,
        'abc :-)': 1,
        ':-) abc': 1,
        'a :-) b': 1,
    }

    def setUp(self):
        cache.clear()
        self.addCleanup(cache.clear)

    def test_each_padded_code_renders_as_an_image(self):
        for text, count in self.PADDED.items():
            with self.subTest(text=text):
                self.assertEqual(site_markup(text).count('<img '), count)

    def test_an_unpadded_code_stays_text(self):
        self.assertNotIn('<img ', site_markup('ab:-)cd'))
