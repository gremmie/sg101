"""
import_old_news_comments.py - For importing comments on news stories from SG101 1.0 as csv files.
"""
from __future__ import with_statement
import csv
import optparse
import sys
from datetime import datetime

from django.core.management.base import LabelCommand, CommandError
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType

from comments.models import Comment
from news.models import Story
import legacy.data
from legacy.html2md import MarkdownWriter


class Command(LabelCommand):
    args = '<filename filename ...>'
    help = 'Imports news story comments from the old database in CSV format'
    option_list = LabelCommand.option_list + (
        optparse.make_option("-p", "--progress", action="store_true",
            help="Output a . after every 20 comments to show progress"),
    )
    md_writer = MarkdownWriter()

    def handle_label(self, filename, **options):
        """
        Process each line in the CSV file given by filename by
        creating a new story comment.

        """
        self.show_progress = options.get('progress')
        self.users = {}

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
        Process one row from the CSV file: create a Comment object for
        the row and save it in the database.

        """
        row = dict((k, v if v != 'NULL' else '') for k, v in row.iteritems())

        try:
            user = self._get_user(row['name'])
        except User.DoesNotExist:
            print "Could not find user %s for comment %s; skipping." % (
                    row['name'], row['tid'])
            return

        try:
            story = Story.objects.get(id=int(row['sid']))
        except Story.DoesNotExist:
            print "Could not find story %s for comment %s; skipping." % (
                    row['sid'], row['tid'])
            return

        comment = Comment(
            id=int(row['tid']),
            content_type = ContentType.objects.get_for_model(story),
            object_id = story.id,
            user = user,
            comment = self.to_markdown(row['comment']),
            creation_date = datetime.strptime(row['date'], "%Y-%m-%d %H:%M:%S"),
            ip_address = row['host_name'],
            is_public = True,
            is_removed = False,
        )

        comment.save()

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
                user = User.objects.get(
                        username=legacy.data.KNOWN_USERNAME_CHANGES[username])
            except KeyError:
                raise User.DoesNotExist

        self.users[username] = user
        return user

    def to_markdown(self, s):
        self.md_writer.reset()

        if not isinstance(s, unicode):
            s = s.decode('utf-8', 'replace')

        self.md_writer.feed(s)
        return self.md_writer.markdown()
