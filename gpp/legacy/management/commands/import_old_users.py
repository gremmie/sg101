"""
import_old_users.py - For importing users from SG101 1.0 as csv files.
"""
from __future__ import with_statement
import csv
import optparse
import re
import sys
from datetime import datetime

import postmarkup

from django.core.management.base import LabelCommand, CommandError
from django.contrib.auth.models import User

import bio.models
from legacy.phpbb import unphpbb
from legacy.html2md import MarkdownWriter

TIME_ZONES = {
    '-5': 'US/Eastern',
    '-6': 'US/Central',
    '-7': 'US/Mountain',
    '-8': 'US/Pacific',
}
USERNAME_RE = re.compile(r'^[\w.@+-]+$')
USERNAME_LEN = (1, 30)      # min & max length values


def _valid_username(username):
    """
    Return true if the username is valid.
    """
    return (USERNAME_LEN[0] <= len(username) <= USERNAME_LEN[1] and
            USERNAME_RE.match(username))


def _break_name(name):
    """
    Break name into a first and last name.
    Return a 2-tuple of first_name, last_name.
    """
    parts = name.split()
    n = len(parts)
    if n == 0:
        t = '', ''
    elif n == 1:
        t = parts[0], ''
    else:
        t = ' '.join(parts[:-1]), parts[-1]
    return t[0][:USERNAME_LEN[1]], t[1][:USERNAME_LEN[1]]


class Command(LabelCommand):
    args = '<filename filename ...>'
    help = 'Imports users from the old database in CSV format'
    option_list = LabelCommand.option_list + (
        optparse.make_option("-s", "--super-user",
            help="Make the user with this name a superuser"),
        optparse.make_option("-a", "--anon-user",
            help="Make the user with this name the anonymous user "
                "[default: Anonymous]"),
        optparse.make_option("-p", "--progress", action="store_true",
            help="Output a . after every 20 users to show progress"),
    )
    bb_parser = postmarkup.create(use_pygments=False, annotate_links=False)
    md_writer = MarkdownWriter()

    def handle_label(self, filename, **options):
        """
        Process each line in the CSV file given by filename by
        creating a new user and profile.

        """
        self.superuser = options.get('super_user')
        self.anonymous = options.get('anon_user')
        if self.anonymous is None:
            self.anonymous = 'Anonymous'
        self.show_progress = options.get('progress')

        if self.superuser == self.anonymous:
            raise CommandError("super-user name should not match anon-user")

        try:
            with open(filename, "rb") as f:
                self.reader = csv.DictReader(f)
                num_rows = 0
                try:
                    for row in self.reader:
                        self.process_row(row)
                        num_rows += 1
                        if num_rows % 20 == 0:
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
        Process one row from the CSV file: create a user and user profile for
        the row and save it in the database.

        """
        row = dict((k, v if v != 'NULL' else '') for k, v in row.iteritems())

        if not _valid_username(row['username']):
            print "Skipping import of %s; invalid username" % row['username']
            return

        n = User.objects.filter(username=row['username']).count()
        if n > 0:
            print "Skipping import of %s; user already exists" % row['username']
            return

        first_name, last_name = _break_name(row['name'])
        is_superuser = self.superuser == row['username']
        is_anonymous = self.anonymous == row['username']

        u = User(id=int(row['user_id']),
                username=row['username'],
                first_name=first_name,
                last_name=last_name,
                email=row['user_email'],
                password=row['user_password'] if row['user_password'] else None,
                is_staff=is_superuser,
                is_active=True if not is_anonymous else False,
                is_superuser=is_superuser,
                last_login=datetime.fromtimestamp(int(row['user_lastvisit'])),
                date_joined=datetime.strptime(row['user_regdate'], "%b %d, %Y"))

        if is_anonymous:
            u.set_unusable_password()

        u.save()

        p = u.get_profile()
        p.location = row['user_from']
        p.occupation = row['user_occ']
        p.interests = row['user_interests']
        p.profile_text = u''
        p.hide_email = True if row['user_viewemail'] != '1' else False
        p.signature = self.to_markdown(row['user_sig']) if row['user_sig'] else u''
        p.time_zone = TIME_ZONES.get(row['user_timezone'], 'US/Pacific')
        p.use_24_time = False
        p.forum_post_count = int(row['user_posts'])
        p.status = bio.models.STA_ACTIVE if p.forum_post_count > 10 else bio.models.STA_STRANGER
        p.status_date = datetime.now()
        p.update_date = p.status_date
        p.save()

    def to_html(self, s):
        return self.bb_parser.render_to_html(unphpbb(s), cosmetic_replace=False)

    def to_markdown(self, s):
        self.md_writer.reset()
        self.md_writer.feed(self.to_html(s))
        return self.md_writer.markdown()
