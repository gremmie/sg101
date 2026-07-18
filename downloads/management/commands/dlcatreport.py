"""
dlcatreport - a management command to produce a HTML report of all the downloads
in a given category.

"""
from django.core import serializers
from django.core.management.base import LabelCommand, CommandError
from django.template.loader import render_to_string

from downloads.models import Category, Download


class Command(LabelCommand):
    help = "Produce on standard output a report of all downloads in a category."

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)
        parser.add_argument('--titles-only',
                action='store_true',
                default=False,
                help='Output a text listing of titles only')
        parser.add_argument('--json',
                action='store_true',
                default=False,
                help='Output downloads in JSON format')

    def handle_label(self, slug, **options):
        """
        Render a template using the downloads in a given category and send it to
        stdout.

        """
        try:
            category = Category.objects.get(slug=slug)
        except Category.DoesNotExist:
            raise CommandError("category slug '%s' does not exist" % slug)

        downloads = Download.public_objects.filter(category=category).order_by(
                'title').select_related()

        if options.get('titles_only'):
            self.print_titles(downloads)
            return

        if options.get('json'):
            self.print_json(downloads)
            return

        report = render_to_string('downloads/commands/category_report.html', {
            'category': category,
            'downloads': downloads,
            })

        self.stdout.write(report)

    def print_titles(self, dls):
        """Print out the download titles"""

        for dl in dls:
            self.stdout.write(dl.title)

    def print_json(self, dls):
        """Output downloads in JSON format"""
        data = serializers.serialize('json', dls)
        self.stdout.write(data)


