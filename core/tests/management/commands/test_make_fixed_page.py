"""Test for the make_fixed_page management command."""
from io import StringIO
import os.path
import shutil
import tempfile
import textwrap
import unittest

from django.core.management import call_command
from mock import patch


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

    def setUp(self):
        # Create temp directory structure.
        self.temp_root = tempfile.mkdtemp()
        fixed_dir = os.path.join(self.temp_root, 'fixed')
        os.mkdir(fixed_dir)

        self.template_dir = os.path.join(self.temp_root, 'templates', 'fixed')
        os.makedirs(self.template_dir)

        # Create a sample .rst file to work with.
        self.temp_rst = os.path.join(fixed_dir, 'sample.rst')
        fp = open(self.temp_rst, mode='w')
        fp.write(self.RST_SAMPLE)
        fp.close()

    def tearDown(self):
        shutil.rmtree(self.temp_root)

    def test_make_fixed_page(self):
        out = StringIO()
        with patch('core.management.commands.make_fixed_page.settings'
                   '.PROJECT_PATH', new=self.temp_root):
            call_command('make_fixed_page', 'sample.rst', stdout=out)
            self.assertEqual(out.getvalue(),
                             'sample.rst -> templates/fixed/sample.html\n')
        out.close()
        with open(os.path.join(self.template_dir, 'sample.html')) as fp:
            self.assertEqual(fp.read(), self.EXPECTED_HTML)
