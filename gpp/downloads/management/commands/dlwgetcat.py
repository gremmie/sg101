"""
dlwgetcat - a management command to produce a bash script that wgets all the
files in a given category.

"""
import os.path

from django.core.management.base import LabelCommand, CommandError
from django.template.loader import render_to_string
from django.template.defaultfilters import slugify
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

        current_site = Site.objects.get_current()

        # Create new destination names for the files since the uploaders often
        # give the files terrible names. The new names will be slugified
        # versions of the titles, with the same extension.

        for dl in downloads:
            ext = os.path.splitext(dl.file.name)[1]
            dl.dest_filename = slugify(dl.title) + ext

            # build a full URL to the download
            dl.full_url = 'http://%s%s%s' % (current_site.domain,
                    settings.MEDIA_URL, dl.file.name)

        output = render_to_string('downloads/commands/wget_cat.html', {
            'downloads': downloads,
            })

        # encode it ourselves since it can fail if you try to redirect output to
        # a file and any of the content is not ASCII...
        print output.encode('utf-8')
