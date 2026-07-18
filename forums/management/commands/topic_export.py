"""
topic_export.py

A management command to export a forum topic by rendering it through a given
template.

"""
from __future__ import with_statement
import re

from django.conf import settings
from django.core.management.base import LabelCommand, CommandError
from django.template.loader import render_to_string, TemplateDoesNotExist

from forums.models import Topic


SRC_RE = re.compile(r'src="/media/')
SRC_REPL = 'src="{}://surfguitar101.com/media/'.format(settings.SITE_SCHEME)


class Command(LabelCommand):
    help = "Exports a forum topic thread by rendering it through a given template"

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)
        parser.add_argument('-t', '--template',
                        default='forums/topic_export.html',
                        help='template to render')
        parser.add_argument('-o', '--output',
                        default=None,
                        help='output filename [default: stdout]')

    def handle_label(self, tid, **opts):
        """Fetch the topic and related posts. Render through a template.
        Optionally write content to an output file.

        """
        try:
            tid = int(tid)
        except ValueError:
            raise CommandError('topic ID must be an integer')

        template_name = opts['template']
        output_filename = opts['output']

        try:
            topic = Topic.objects.get(pk=tid)
        except Topic.DoesNotExist:
            raise CommandError('topic ID does not exist')

        posts = topic.posts.select_related('user')

        try:
            content = render_to_string(template_name, {'topic': topic, 'posts':
                posts})
        except TemplateDoesNotExist:
            raise CommandError('template does not exist')

        # fix up smiley images
        content = SRC_RE.sub(SRC_REPL, content)

        content = content.encode('utf-8')

        if output_filename:
            with open(output_filename, 'w') as fp:
                fp.write(content)
        else:
            self.stdout.write(content)
