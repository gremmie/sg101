"""
import_old_topics.py - For importing forum topics (threads) from SG101 1.0 as
csv files.

"""
from __future__ import with_statement
import csv
import optparse
import sys
from datetime import datetime

from django.core.management.base import LabelCommand, CommandError
from django.contrib.auth.models import User

from forums.models import Forum, Topic
from legacy.phpbb import unescape


class Command(LabelCommand):
    args = '<filename filename ...>'
    help = 'Imports forum topics from the old database in CSV format'
    option_list = LabelCommand.option_list + (
        optparse.make_option("-p", "--progress", action="store_true",
            help="Output a . after every 20 topics to show progress"),
    )

    def handle_label(self, filename, **options):
        """
        Process each line in the CSV file given by filename by
        creating a new topic.

        """
        self.show_progress = options.get('progress')
        self.users = {}

        # Create a mapping from the old database's forums to our
        # forums
        self.forums = {}
        try:
            self.forums[2] = Forum.objects.get(slug='suggestion-box')
            self.forums[3] = Forum.objects.get(slug='surf-music')
            self.forums[4] = Forum.objects.get(slug='surf-musician')
            self.forums[5] = Forum.objects.get(slug='gear')
            self.forums[6] = Forum.objects.get(slug='recording-corner')
            self.forums[7] = Forum.objects.get(slug='shallow-end')
            self.forums[8] = Forum.objects.get(slug='surfguitar101-website')
            self.forums[9] = Forum.objects.get(id=15)
            self.forums[10] = Forum.objects.get(slug='for-sale-trade')
            self.forums[11] = Forum.objects.get(slug='musicians-gigs-wanted')
            self.forums[12] = Forum.objects.get(slug='surf-videos')
            self.forums[13] = Forum.objects.get(slug='sg101-podcast')
            self.forums[14] = Forum.objects.get(slug='gigs')
            self.forums[15] = Forum.objects.get(slug='music-reviews')
            self.forums[18] = Forum.objects.get(slug='best-sg101')
        except Forum.DoesNotExist:
            sys.exit("Forum does not exist; check forum mapping.")

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

        if row['topic_moved_id'] != '0':
            return

        try:
            user = User.objects.get(id=int(row['topic_poster']))
        except User.DoesNotExist:
            print "Could not find user %s for topic %s; skipping." % (
                    row['topic_poster'], row['topic_id'])
            return

        creation_date = datetime.fromtimestamp(float(row['topic_time']))

        title = row['topic_title'].decode('latin-1', 'replace')

        try:
            forum = self.forums[int(row['forum_id'])]
        except KeyError:
            print 'skipping topic "%s"' % title
            return

        topic = Topic(id=int(row['topic_id']),
                forum=forum,
                name=unescape(title),
                creation_date=creation_date,
                user=user,
                view_count=int(row['topic_views']),
                sticky=(int(row['topic_type']) != 0),
                locked=(int(row['topic_status']) != 0),
                update_date=creation_date)

        topic.save()

