"""
import_old_potd.py - For importing POTD's from SG101 1.0 as csv files.

"""
from __future__ import with_statement
import csv
import optparse
import sys
from datetime import datetime

from django.core.management.base import LabelCommand, CommandError
from django.contrib.auth.models import User

from potd.models import Photo
from legacy.phpbb import unescape
import legacy.data


ID_OFFSET = 100


class PathError(Exception):
    pass

def convert_path(old_path):
    """
    Converts the old POTD path to a new one.

    """
    if old_path.startswith('images/potd/'):
        return "potd/1.0/%s" % old_path[12:]
    else:
        raise PathError("Unknown path %s" % old_path)


class Command(LabelCommand):
    args = '<filename filename ...>'
    help = "Imports POTD's from the old database in CSV format"
    option_list = LabelCommand.option_list + (
        optparse.make_option("-p", "--progress", action="store_true",
            help="Output a . after every 20 items to show progress"),
    )

    def handle_label(self, filename, **options):
        """
        Process each line in the CSV file given by filename by
        creating a new Photo

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
        Process one row from the CSV file: create a Photo object for
        the row and save it in the database.

        """
        try:
            submitter = self._get_user(row['submitted_by'].decode('latin-1'))
        except User.DoesNotExist:
            print "Could not find user %s for potd %s; skipping." % (
                    row['submitted_by'], row['pid'])
            return

        desc = row['description'].decode('latin-1').replace('\n', '\n<br />')

        try:
            photo = Photo(
                id=int(row['pid']) + ID_OFFSET,
                photo=convert_path(row['photo_path']),
                thumb=convert_path(row['thumb_path']),
                caption=unescape(row['title'].decode('latin-1')),
                description=desc,
                user=submitter,
                date_added=datetime.strptime(row['date_added'],
                    "%Y-%m-%d %H:%M:%S"),
                potd_count=int(row['chosen_count']))
        except PathError, ex:
            self.stderr.write("\n%s, skipping\n" % ex)
            return

        photo.save()

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
