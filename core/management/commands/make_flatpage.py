"""make_flatpage.py

A management command to update flatpage objects from restructured text files.

"""
import os.path

import docutils.core
from django.core.management.base import LabelCommand, CommandError
from django.conf import settings
from django.template.loader import render_to_string
from django.template import TemplateDoesNotExist
from django.contrib.flatpages.models import FlatPage


class Command(LabelCommand):
    help = "Update flatpage objects from restructured text files"
    args = "<inputfile1> <inputfile2> ... | all"

    def handle_label(self, filename, **kwargs):
        """Process input file(s)"""

        if not hasattr(settings, 'GPP_FLATPAGES'):
            raise CommandError("Please add a GPP_FLATPAGES setting")
        if not hasattr(settings, 'PROJECT_PATH'):
            raise CommandError("Please add a PROJECT_PATH setting")

        self.config = settings.GPP_FLATPAGES
        self.src_dir = os.path.join(settings.PROJECT_PATH, 'flatpages')

        if filename == 'all':
            files = self.config.keys()
        else:
            files = [filename]

        for f in files:
            self.process_flatpage(f)


    def process_flatpage(self, filename):
        """Processes one flatpage"""

        if filename not in self.config:
            raise CommandError("No entry in GPP_FLATPAGES for %s" % filename)
        url, template_name = self.config[filename]

        # retrieve source text
        src_path = os.path.join(self.src_dir, filename)
        with open(src_path, 'r') as f:
            src_text = f.read()

        # transform text
        content = self.transform_input(src_text)

        # render through a template if requested
        if template_name is not None:
            try:
                content = render_to_string(template_name, dict(content=content))
            except TemplateDoesNotExist:
                raise CommandError("template not found: %s" % template_name)

        # update the flatpage object
        try:
            obj = FlatPage.objects.get(url=url)
        except FlatPage.DoesNotExist:
            raise CommandError("flatpage not found: %s" % url)

        obj.content = content;
        obj.save()

        self.stdout.write("%s -> %s\n" % (filename, url))

    def transform_input(self, src_text):
        """Transforms input restructured text to HTML"""

        return docutils.core.publish_parts(src_text, writer_name='html',
                settings_overrides={
                    'doctitle_xform': False,
                    'initial_header_level': 3,
                    })['html_body']
