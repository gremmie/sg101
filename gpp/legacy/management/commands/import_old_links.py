"""
import_old_links.py - For importing links from SG101 1.0 as csv files.
"""
from __future__ import with_statement
import csv
import datetime

from django.core.management.base import LabelCommand, CommandError
from django.contrib.auth.models import User

from weblinks.models import Link, Category


class Command(LabelCommand):
    args = '<filename filename ...>'
    help = 'Imports weblinks from the old database in CSV format'

    def handle_label(self, filename, **options):
        """
        Process each line in the CSV file given by filename by
        creating a new weblink object and saving it to the database.

        """
        self.cats = {}
        try:
            self.default_user = User.objects.get(pk=2)
        except User.DoesNotExist:
            raise CommandError("Need a default user with pk=1")

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

    def get_category(self, row):
        """
        Return the Category object for the row.

        """
        cat_id = row['cid']
        if cat_id not in self.cats:
            try:
                cat = Category.objects.get(pk=cat_id)
            except Category.DoesNotExist:
                raise CommandError("Category does not exist: %s on line %s" % (
                    cat_id, self.reader.line_num))
            else:
                self.cats[cat_id] = cat
        return self.cats[cat_id]

    def get_user(self, username):
        """
        Return the user object for the given username.
        If the user cannot be found, self.default_user is returned.

        """
        try:
            return User.objects.get(username=username)
        except User.DoesNotExist:
            return self.default_user

    def process_row(self, row):
        """
        Process one row from the CSV file: create an object for the row
        and save it in the database.

        """
        link = Link(category=self.get_category(row),
            title=row['title'].decode('latin-1'),
            url=row['url'].decode('latin-1'),
            description=row['description'].decode('latin-1'),
            user=self.get_user(row['submitter']),
            date_added=datetime.datetime.strptime(row['date'], "%Y-%m-%d %H:%M:%S"),
            hits=int(row['hits']),
            is_public=True)
        link.save()
