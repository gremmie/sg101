"""
dlcatreport - a management command to produce a HTML report of all the downloads
in a given category.

"""
from optparse import make_option

from django.core.management.base import LabelCommand, CommandError
from django.template.loader import render_to_string

from downloads.models import Category, Download


class Command(LabelCommand):
    help = "Produce on standard output a report of all downloads in a category."
    args = "category-slug"

    option_list = LabelCommand.option_list + (
            make_option('--titles-only',
                action='store_true',
                default=False,
                help='Output a text listing of titles only'),
            )

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

        report = render_to_string('downloads/commands/category_report.html', {
            'category': category,
            'downloads': downloads,
            })

        # encode it ourselves since it can fail if you try to redirect output to
        # a file and any of the content is not ASCII...
        self.stdout.write(report.encode('utf-8'))

    def print_titles(self, dls):
        """Print out the download titles"""

        for dl in dls:
            self.stdout.write(dl.title.encode('utf-8'))


