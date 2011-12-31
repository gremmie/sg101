"""
import_old_potd_comments.py - For importing comments on POTD's from SG101 1.0
as csv files.

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
from potd.models import Photo
import legacy.data
from legacy.html2md import MarkdownWriter


PHOTO_ID_OFFSET = 100
ID_OFFSET = 3000


class Command(LabelCommand):
    args = '<filename filename ...>'
    help = 'Imports POTD comments from the old database in CSV format'
    option_list = LabelCommand.option_list + (
        optparse.make_option("-p", "--progress", action="store_true",
            help="Output a . after every 20 items to show progress"),
    )
    md_writer = MarkdownWriter()

    def handle_label(self, filename, **options):
        """
        Process each line in the CSV file given by filename by
        creating a new POTD comment.

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
        try:
            user = self._get_user(row['username'].decode('latin-1'))
        except User.DoesNotExist:
            print "Could not find user %s for comment %s; skipping." % (
                    row['username'], row['cid'])
            return

        pid = int(row['pid']) + PHOTO_ID_OFFSET
        try:
            photo = Photo.objects.get(id=pid)
        except Photo.DoesNotExist:
            print "Could not find photo %s for comment %s; skipping." % (
                    pid, row['cid'])
            return

        comment = Comment(
            id=int(row['cid']) + ID_OFFSET,
            content_type=ContentType.objects.get_for_model(photo),
            object_id=photo.id,
            user=user,
            comment=self.to_markdown(row['comment'].decode('latin-1')),
            creation_date=datetime.strptime(row['date'], "%Y-%m-%d %H:%M:%S"),
            ip_address='192.0.2.0',     # TEST-NET
            is_public=True,
            is_removed=False,
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
            old_name = username.lower()
            try:
                user = User.objects.get(
                        username=legacy.data.KNOWN_USERNAME_CHANGES[old_name])
            except KeyError:
                raise User.DoesNotExist

        self.users[username] = user
        return user

    def to_markdown(self, s):

        s = s.replace('\n', '\n<br />')
        self.md_writer.reset()
        self.md_writer.feed(s)
        return self.md_writer.markdown()
