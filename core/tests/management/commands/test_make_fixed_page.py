"""Test for the make_fixed_page management command."""
from io import StringIO
import os.path
import shutil
import tempfile
import textwrap
import unittest

from django.core.management import call_command
from django.core.management.base import CommandError
from unittest.mock import patch


class MakeFixedPageTestCase(unittest.TestCase):
    RST_SAMPLE = textwrap.dedent("""\
        ========
        Test RST
        ========

        Here is some sample text.
    """)

    EXPECTED_HTML = textwrap.dedent("""\
        <div class="document">
        <div class="section" id="test-rst">
        <h2>Test RST</h2>
        <p>Here is some sample text.</p>
        </div>
        </div>
    """)

    MD_SAMPLE = textwrap.dedent("""\
        ## Test MD

        Here is some [sample][1] text,
        wrapped across two lines.

        [1]: https://example.com/
    """)

    EXPECTED_MD_HTML = textwrap.dedent("""\
        <h2>Test MD</h2>
        <p>Here is some <a href="https://example.com/">sample</a> text,
        wrapped across two lines.</p>""")

    def setUp(self):
        # Create temp directory structure.
        self.temp_root = tempfile.mkdtemp()
        self.fixed_dir = os.path.join(self.temp_root, 'fixed')
        os.mkdir(self.fixed_dir)

        self.template_dir = os.path.join(self.temp_root, 'templates', 'fixed')
        os.makedirs(self.template_dir)

        # Create a sample .rst file to work with.
        self.write_source('sample.rst', self.RST_SAMPLE)

    def tearDown(self):
        shutil.rmtree(self.temp_root)

    def write_source(self, filename, text):
        with open(os.path.join(self.fixed_dir, filename), 'w') as fp:
            fp.write(text)

    def read_output(self, filename):
        with open(os.path.join(self.template_dir, filename)) as fp:
            return fp.read()

    def make_fixed_page(self, label):
        out = StringIO()
        with patch('core.management.commands.make_fixed_page.settings'
                   '.PROJECT_PATH', new=self.temp_root):
            call_command('make_fixed_page', label, stdout=out)
        return out.getvalue()

    def test_make_fixed_page(self):
        self.assertEqual(self.make_fixed_page('sample.rst'),
                         'sample.rst -> templates/fixed/sample.html\n')
        self.assertEqual(self.read_output('sample.html'), self.EXPECTED_HTML)

    def test_markdown(self):
        self.write_source('other.md', self.MD_SAMPLE)
        self.assertEqual(self.make_fixed_page('other.md'),
                         'other.md -> templates/fixed/other.html\n')
        self.assertEqual(self.read_output('other.html'), self.EXPECTED_MD_HTML)

    def test_all_includes_markdown(self):
        self.write_source('other.md', self.MD_SAMPLE)
        self.make_fixed_page('all')
        self.assertEqual(self.read_output('sample.html'), self.EXPECTED_HTML)
        self.assertEqual(self.read_output('other.html'), self.EXPECTED_MD_HTML)

    def test_unknown_extension(self):
        self.write_source('other.txt', 'Some text.\n')
        with self.assertRaisesRegex(CommandError, 'other.txt'):
            self.make_fixed_page('other.txt')
        self.assertFalse(os.path.exists(
            os.path.join(self.template_dir, 'other.html')))

    def test_all_refuses_two_sources_for_one_page(self):
        self.write_source('sample.md', self.MD_SAMPLE)
        with self.assertRaisesRegex(CommandError, 'sample'):
            self.make_fixed_page('all')
        self.assertFalse(os.path.exists(
            os.path.join(self.template_dir, 'sample.html')))
