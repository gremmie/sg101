"""
This command calls save() on all bandmap entries.

This causes the html field to be rebuilt. This is the text displayed inside the
"balloon" on the map when a band's marker is clicked.

"""
from django.core.management.base import NoArgsCommand

from bandmap.models import BandEntry


class Command(NoArgsCommand):
    help = "This command rebuilds the html field on all bandmap entries."

    def handle_noargs(self, **kwargs):

        for band in BandEntry.objects.all().iterator():
            band.save()
