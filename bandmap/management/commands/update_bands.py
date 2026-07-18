"""
This command calls save() on all bandmap entries.

This causes the html field to be rebuilt. This is the text displayed inside the
"balloon" on the map when a band's marker is clicked.

"""
from django.core.management.base import BaseCommand

from bandmap.models import BandEntry


class Command(BaseCommand):
    help = "This command rebuilds the html field on all bandmap entries."

    def handle(self, *args, **kwargs):

        for band in BandEntry.objects.all().iterator():
            band.save()
