"""
import_old_downloads.py - For importing downloads from SG101 1.0 as csv files.
"""
from __future__ import with_statement
import csv
import datetime

from django.core.management.base import LabelCommand, CommandError
from django.contrib.auth.models import User

from downloads.models import Download, Category
from legacy.html2md import MarkdownWriter


# downloads with these lid's will be excluded
EXCLUDE_SET = set([1, 2, 3, 4, 277])

# Mapping of old category IDs to new; None means we don't plan on importing
CAT_MAP = {
  4: None,      # Misc
  3: None,      # Music
  1: None,      # Demos
  6: 2,         # Gear Samples
  8: 4,         # Ringtones
  9: 8,         # Tablature
  10: 6,        # Interviews
  11: None,     # 2008 MP3 Comp
  12: 1,        # Backing Tracks
  13: None,     # 2009 MP3 Comp
}

SG101_PREFIX = 'http://surfguitar101.com/'


class Command(LabelCommand):
    args = '<filename filename ...>'
    help = 'Imports downloads from the old database in CSV format'
    md_writer = MarkdownWriter()

    def handle_label(self, filename, **options):
        """
        Process each line in the CSV file given by filename by
        creating a new object and saving it to the database.

        """
        self.cats = {}
        try:
            self.default_user = User.objects.get(pk=2)
        except User.DoesNotExist:
            raise CommandError("Need a default user with pk=2")

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

    def get_category(self, old_cat_id):
        """
        Return the Category object for the row.

        """
        cat_id = CAT_MAP[old_cat_id]
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
        lid = int(row['lid'])
        if lid in EXCLUDE_SET:
            return  # skip

        cat = int(row['cid'])
        if CAT_MAP.get(cat) is None:
            return  # skip this one; we aren't carrying these over

        dl_date = datetime.datetime.strptime(row['date'], "%Y-%m-%d %H:%M:%S")
        old_url = row['url'].decode('latin-1')
        if old_url.startswith(SG101_PREFIX):
            old_url = old_url[len(SG101_PREFIX):]
        if old_url.startswith('dls/'):
            old_url = old_url[4:]
        new_url = u'downloads/1.0/%s' % old_url

        dl = Download(
            id=lid,
            title=row['title'].decode('latin-1'),
            category=self.get_category(cat),
            description=self.to_markdown(row['description'].decode('latin-1')),
            file=new_url,
            user=self.get_user(row['submitter']),
            date_added=dl_date,
            ip_address='127.0.0.1',  # not available
            hits=int(row['hits']),
            average_score=float(row['downloadratingsummary']) / 2.0,
            total_votes=int(row['totalvotes']),
            is_public=True)
        dl.save()
        #print "cp %s %s" % (old_url, '/home/var/django-sites/sg101/sg101-trunk/media/' + new_url)

    def to_markdown(self, s):
        self.md_writer.reset()
        self.md_writer.feed(s)
        return self.md_writer.markdown()
