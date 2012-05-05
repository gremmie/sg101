"""
import_old_podcasts.py - For importing podcasts from SG101 1.0 as csv files.
"""
from __future__ import with_statement
import csv
import datetime

from django.core.management.base import LabelCommand, CommandError

from podcast.models import Channel, Item


class Command(LabelCommand):
    args = '<filename filename ...>'
    help = 'Imports podcasts from the old database in CSV format'

    def handle_label(self, filename, **options):
        """
        Process each line in the CSV file given by filename by
        creating a new weblink object and saving it to the database.

        """
        try:
            self.channel = Channel.objects.get(pk=1)
        except Channel.DoesNotExist:
            raise CommandError("Need a default channel with pk=1")

        try:
            with open(filename, "rb") as f:
                self.reader = csv.DictReader(f)
                try:
                    for row in self.reader:
                        self.process_row(row)
                except csv.Error, e:
                    raise CommandError("CSV error: %s %s %s" % (
                        filename, self.reader.line_num, e))

        except IOError:
            raise CommandError("Could not open file: %s" % filename)

    def process_row(self, row):
        """
        Process one row from the CSV file: create an object for the row
        and save it in the database.

        """
        item = Item(channel=self.channel,
            title=row['title'],
            author=row['author'],
            subtitle=row['subtitle'],
            summary=row['summary'],
            enclosure_url=row['enclosure_url'],
            alt_enclosure_url='',
            enclosure_length=int(row['enclosure_length']),
            enclosure_type=row['enclosure_type'],
            guid=row['guid'],
            pubdate=datetime.datetime.strptime(row['pubdate'],
                "%Y-%m-%d %H:%M:%S"),
            duration=row['duration'],
            keywords=row['keywords'],
            explicit=row['explicit'])

        item.save()
