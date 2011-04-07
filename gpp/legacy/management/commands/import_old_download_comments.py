"""
import_old_download_comments.py - For importing download comments from SG101 1.0
as csv files.

"""
from __future__ import with_statement
import csv
from datetime import datetime

from django.core.management.base import LabelCommand, CommandError
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType

from downloads.models import Download, VoteRecord
from comments.models import Comment
from legacy.html2md import MarkdownWriter
import legacy.data


class Command(LabelCommand):
    args = '<filename filename ...>'
    help = 'Imports download comments from the old database in CSV format'
    md_writer = MarkdownWriter()

    def handle_label(self, filename, **options):
        """
        Process each line in the CSV file given by filename by
        creating a new object and saving it to the database.

        """
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
        dl_id = int(row['ratinglid'])
        if dl_id in (1, 2, 3, 4):
            return

        try:
            dl = Download.objects.get(pk=dl_id)
        except Download.DoesNotExist:
            return

        try:
            user = User.objects.get(username=row['ratinguser'])
        except User.DoesNotExist:
            try:
                user = User.objects.get(
                    username=legacy.data.KNOWN_USERNAME_CHANGES[row['ratinguser']])
            except (User.DoesNotExist, KeyError):
                return

        vote_date = datetime.strptime(row['ratingtimestamp'], "%Y-%m-%d %H:%M:%S")

        comment_text = row['ratingcomments'].decode('latin-1').strip()
        if comment_text:
            comment = Comment(
                content_type=ContentType.objects.get_for_model(dl),
                object_id=dl.id,
                user=user,
                comment=comment_text,
                creation_date=vote_date,
                ip_address = row['ratinghostname'],
                is_public = True,
                is_removed = False,
            )
            comment.save()

        vr = VoteRecord(download=dl, user=user, vote_date=vote_date)
        vr.save()

    def to_markdown(self, s):
        self.md_writer.reset()
        self.md_writer.feed(s)
        return self.md_writer.markdown()
