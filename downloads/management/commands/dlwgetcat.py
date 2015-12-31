"""
dlwgetcat - a management command to produce a bash script that wgets all the
files in a given category.

"""
import os.path

from django.core.management.base import LabelCommand, CommandError
from django.template.loader import render_to_string
from django.utils.text import slugify
from django.contrib.sites.models import Site
from django.conf import settings

from downloads.models import Category, Download


class Command(LabelCommand):
    help = ("Produce on standard output a bash script that wgets all the files"
            " in a category. The files are downloaded with a slugified name.")

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

        # Create new destination names for the files since the uploaders often
        # give the files terrible names. The new names will be slugified
        # versions of the titles, with the same extension.

        for dl in downloads:
            ext = os.path.splitext(dl.file.name)[1]
            dl.dest_filename = slugify(dl.title) + ext

        base_url = "{}://{}{}".format(settings.SITE_SCHEME,
                                      Site.objects.get_current().domain,
                                      settings.MEDIA_URL)

        output = render_to_string('downloads/commands/wget_cat.html', {
            'downloads': downloads,
            'base_url': base_url,
            })

        self.stdout.write(output)
