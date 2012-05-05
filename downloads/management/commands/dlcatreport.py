"""
dlcatreport - a management command to produce a HTML report of all the downloads
in a given category.

"""
from django.core.management.base import LabelCommand, CommandError
from django.template.loader import render_to_string

from downloads.models import Category, Download


class Command(LabelCommand):
    help = "Produce on standard output a report of all downloads in a category."
    args = "category-slug"

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

        report = render_to_string('downloads/commands/category_report.html', {
            'category': category,
            'downloads': downloads,
            })

        # encode it ourselves since it can fail if you try to redirect output to
        # a file and any of the content is not ASCII...
        print report.encode('utf-8')

