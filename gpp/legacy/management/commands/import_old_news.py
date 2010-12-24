"""
import_old_news.py - For importing news stories from SG101 1.0 as csv files.
"""
from __future__ import with_statement
import csv
import optparse
import sys
from datetime import datetime

from django.core.management.base import LabelCommand, CommandError
from django.contrib.auth.models import User

from news.models import Category, Story
from legacy.phpbb import unescape

KNOWN_USERNAME_CHANGES = {
    'cavefishbutchdelux': 'butchdelux',
    'Findicator1': 'WaveOhhh',
}

class Command(LabelCommand):
    args = '<filename filename ...>'
    help = 'Imports news stories from the old database in CSV format'
    option_list = LabelCommand.option_list + (
        optparse.make_option("-p", "--progress", action="store_true",
            help="Output a . after every 20 stories to show progress"),
    )

    def handle_label(self, filename, **options):
        """
        Process each line in the CSV file given by filename by
        creating a new story.

        """
        self.show_progress = options.get('progress')
        self.users = {}

        # Create a mapping from the old database's topics to our
        # Categories.
        self.topics = {}
        try:
            self.topics[2] = Category.objects.get(slug='site-news')
            self.topics[3] = Category.objects.get(slug='bands')
            self.topics[4] = Category.objects.get(slug='show-announcements')
            self.topics[5] = Category.objects.get(slug='show-reports')
            self.topics[6] = Category.objects.get(slug='gear')
            self.topics[7] = Category.objects.get(slug='reviews')
            self.topics[8] = Category.objects.get(slug='surf-scene-news')
            self.topics[9] = Category.objects.get(slug='articles')
            self.topics[10] = Category.objects.get(slug='interviews')
            self.topics[11] = Category.objects.get(slug='tablature')
            self.topics[12] = Category.objects.get(slug='featured-videos')
        except Category.DoesNotExist:
            sys.exit("Category does not exist; check topic mapping.")

        try:
            with open(filename, "rb") as f:
                self.reader = csv.DictReader(f)
                num_rows = 0
                try:
                    for row in self.reader:
                        self.process_row(row)
                        num_rows += 1
                        if self.show_progress and num_rows % 20 == 0:
                            sys.stdout.write('.')
                            sys.stdout.flush()
                except csv.Error, e:
                    raise CommandError("CSV error: %s %s %s" % (
                        filename, self.reader.line_num, e))

                print

        except IOError:
            raise CommandError("Could not open file: %s" % filename)

    def process_row(self, row):
        """
        Process one row from the CSV file: create a Story object for
        the row and save it in the database.

        """
        row = dict((k, v if v != 'NULL' else '') for k, v in row.iteritems())

        try:
            submitter = self._get_user(row['informant'])
        except User.DoesNotExist:
            print "Could not find user %s for story %s; skipping." % (
                    row['informant'], row['sid'])
            return

        story = Story(id=int(row['sid']),
                title=unescape(row['title']),
                submitter=submitter,
                category=self.topics[int(row['topic'])],
                short_text=row['hometext'],
                long_text=row['bodytext'],
                date_submitted=datetime.strptime(row['time'], "%Y-%m-%d %H:%M:%S"),
                allow_comments=True)

        story.save()

    def _get_user(self, username):
        """
        Returns the user object with the given username.
        Throws User.DoesNotExist if not found.

        """
        try:
            return self.users[username]
        except KeyError:
            pass

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            try:
                user = User.objects.get(username=KNOWN_USERNAME_CHANGES[username])
            except KeyError:
                raise User.DoesNotExist

        self.users[username] = user
        return user
