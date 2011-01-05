"""
translate_old_posts.py - A management command to join the bbposts and 
bbposts_text tables together and output as a .csv file, suitable for use as an
input to mysqlimport into the new database. This method bypasses the Django ORM
as it was too slow given the number of old posts to import.

"""
from __future__ import with_statement
import csv
import optparse
from datetime import datetime

import MySQLdb
import postmarkup

from django.core.management.base import NoArgsCommand, CommandError

from legacy.phpbb import unphpbb
from legacy.html2md import MarkdownWriter
from core.markup import SiteMarkup


def convert_ip(s):
    """
    Converts a hex string representing an IP address into dotted notation.
    """
    n = int(s, 16)
    return "%d.%d.%d.%d" % (
            ((n >> 24) & 0xff),
            ((n >> 16) & 0xff),
            ((n >> 8) & 0xff),
            n & 0xff)


class Command(NoArgsCommand):
    help = """\
This command joins converts the SG101 1.0 posts to 2.0 format and outputs the
data as a .csv file suitable for importing into the new database scheme with
the mysqlimport utility.
"""
    option_list = NoArgsCommand.option_list + (
        optparse.make_option("-s", "--progress", action="store_true",
            help="Output a . after every 100 posts to show progress"),
        optparse.make_option("-a", "--host", help="set MySQL host name"),
        optparse.make_option("-u", "--user", help="set MySQL user name"),
        optparse.make_option("-p", "--password", help="set MySQL user password"),
        optparse.make_option("-d", "--database", help="set MySQL database name"),
        optparse.make_option("-o", "--out-file", help="set output filename"),
    )
    bb_parser = postmarkup.create(use_pygments=False, annotate_links=False)
    md_writer = MarkdownWriter()
    site_markup = SiteMarkup()

    def handle_noargs(self, **opts):

        host = opts.get('host', 'localhost') or 'localhost'
        user = opts.get('user', 'root') or 'root'
        password = opts.get('password', '') or ''
        database = opts.get('database')
        out_filename = opts.get('out_file', 'forums_post.csv') or 'forums_post.csv'

        if database is None:
            raise CommandError("Please specify a database option")

        out_file = open(out_filename, "wb")

        # database columns (fieldnames) for the output CSV file:
        cols = ('id', 'topic_id', 'user_id', 'creation_date', 'update_date',
                'body', 'html', 'user_ip')
        self.writer = csv.writer(out_file)

        # Write an initial row of fieldnames to the output file 
        self.writer.writerow(cols)

        # connect to the legacy database
        try:
            db = MySQLdb.connect(host=host,
                    user=user,
                    passwd=password,
                    db=database)
        except MySQLdb.DatabaseError, e:
            raise CommandError(str(e))

        c = db.cursor(MySQLdb.cursors.DictCursor)

        # query the legacy database
        sql = ('SELECT * FROM sln_bbposts as p, sln_bbposts_text as t WHERE '
                'p.post_id = t.post_id ORDER BY p.post_id')
        c.execute(sql)

        # convert the old data and write the output to the file
        while True:
            row = c.fetchone()
            if row is None:
                break

            self.process_row(row)

        c.close()
        db.close()
        out_file.close()

    def to_html(self, s):
        return self.bb_parser.render_to_html(unphpbb(s), cosmetic_replace=False)

    def to_markdown(self, s):
        self.md_writer.reset()
        self.md_writer.feed(self.to_html(s))
        return self.md_writer.markdown()

    def process_row(self, row):
        """
        This function accepts one row from the legacy database and converts the
        contents to the new database format, and calls the writer to write the new
        row to the output file.
        """
        creation_date = datetime.fromtimestamp(float(row['post_time']))

        if row['post_edit_time']:
            update_date = datetime.fromtimestamp(float(row['post_edit_time'])) 
        else:
            update_date = creation_date

        body = self.to_markdown(row['post_text'])
        html = self.site_markup.convert(body)

        self.writer.writerow([row['post_id'],
                row['topic_id'],
                row['poster_id'],
                creation_date,
                update_date,
                body.encode("utf-8"),
                html.encode("utf-8"),
                convert_ip(row['poster_ip'])])
