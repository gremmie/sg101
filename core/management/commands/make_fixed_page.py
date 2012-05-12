"""make_fixed_page.py

A management command to generate HTML files that can be {% include'd %} by a
generic flatpage-like system. We currently support restructured text as input.

I chose "fixed" page since I didn't want to confuse this with Django's flatpage
system.

This command reads input files from the directory PROJECT_PATH/fixed and writes
the HTML output to PROJECT_PATH/templates/fixed.

"""
from __future__ import with_statement
import os.path
import glob

import docutils.core
from django.core.management.base import LabelCommand, CommandError
from django.conf import settings


class Command(LabelCommand):
    help = "Generate HTML from restructured text files"
    args = "<inputfile1> <inputfile2> ... | all"

    def handle_label(self, filename, **kwargs):
        """Process input file(s)"""

        if not hasattr(settings, 'PROJECT_PATH'):
            raise CommandError("Please add a PROJECT_PATH setting")

        self.src_dir = os.path.join(settings.PROJECT_PATH, 'fixed')
        self.dst_dir = os.path.join(settings.PROJECT_PATH, 'templates', 'fixed')

        if filename == 'all':
            files = glob.glob("%s%s*.rst" % (self.src_dir, os.path.sep))
            files = [os.path.basename(f) for f in files]
        else:
            files = [filename]

        for f in files:
            self.process_page(f)

    def process_page(self, filename):
        """Processes one fixed page"""

        # retrieve source text
        src_path = os.path.join(self.src_dir, filename)
        try:
            with open(src_path, 'r') as f:
                src_text = f.read()
        except IOError, ex:
            raise CommandError(str(ex))

        # transform text
        content = self.transform_input(src_text)

        # write output
        basename = os.path.splitext(os.path.basename(filename))[0]
        dst_path = os.path.join(self.dst_dir, '%s.html' % basename)

        try:
            with open(dst_path, 'w') as f:
                f.write(content.encode('utf-8'))
        except IOError, ex:
            raise CommandError(str(ex))

        prefix = os.path.commonprefix([src_path, dst_path])
        self.stdout.write("%s -> %s\n" % (filename, dst_path[len(prefix):]))

    def transform_input(self, src_text):
        """Transforms input restructured text to HTML"""

        return docutils.core.publish_parts(src_text, writer_name='html',
                settings_overrides={
                    'doctitle_xform': False,
                    'initial_header_level': 2,
                    })['html_body']
