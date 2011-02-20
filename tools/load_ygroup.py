"""
load_ygroup.py

This application reads the Yahoo Group posts database and creates .csv files
for populating the ygroup application tables. The .csv files can be used
with the mysqlimport command to load the ygroup_thread and ygroup_post tables.

E.g.:
mysqlimport --fields-optionally-enclosed-by=\" --fields-terminated-by=, --fields-escaped-by="" --lines-terminated-by="\r\n" --user=root --password --local --default-character-set=utf8 gremmies_portal /path/to/ygroup_thread.csv

"""
import csv
import datetime
import optparse
import re
import sys
from email.utils import parseaddr

import MySQLdb


USAGE = "usage: %prog [options]"
DESCRIPTION = """\
This program reads the Yahoo Groups database and outputs 2 .csv files suitable
for import with mysqlimport for loading the ygroup application tables. Threads
and posts are created from the initial data.
"""
###############################################################################

class ConvertPosts(object):
    REPLY_RE = re.compile(r"^Re:", re.IGNORECASE)
    SG101_REPLY_RE = re.compile(r"^Re:\s*\[SurfGuitar101\]", re.IGNORECASE)

    def __init__(self, db, show_progress=False):
        self.db = db
        self.show_progress = show_progress
        self.thread_writer = csv.writer(open('ygroup_thread.csv', 'wb'))
        self.post_writer = csv.writer(open('ygroup_post.csv', 'wb'))
        self.thread_cache = {}
        self.last_date = None

    def process(self):
        """
        Main processing function. Processes a row at a time from the legacy
        database, creating csv records in the thread and posts files as
        appropriate.

        """
        c = self.db.cursor(MySQLdb.cursors.DictCursor)

        # query the legacy database
        sql = "SELECT * FROM post ORDER BY id"
        c.execute(sql)

        # convert the old data and write the output to the file
        i = 0
        while True:
            row = c.fetchone()
            if row is None:
                break
            i += 1
            if i % 100 == 0:
                sys.stdout.write('.')
                sys.stdout.flush()

            self._process_row(row)

        print
        c.close()

    def _process_row(self, row):
        """
        Process one row from the legacy database, creating a csv record
        in the thread or post files as appropriate.

        """
        # Create a unified author name from the Yahoo ID and email address
        # fields in the original post:
        row['author'] = self.get_author(row['name'], row['email'])

        # Some posts (mainly from 1 user...) have no date; we'll just
        # make one up by using the last date we saw + 1 second

        if row['date'] is None:
            assert self.last_date is not None
            row['date'] = self.last_date + datetime.timedelta(seconds=1)

        self.last_date = row['date']

        # determine if this is a new thread or a reply

        if self.REPLY_RE.match(row['title']):
            # This appears to be a reply.
            # Remove all the leading Re: etc., cruft
            stripped_title = self._strip_title(row['title'])
            thread_id = self.thread_cache.get(stripped_title)
            if thread_id:
                self._create_post(thread_id, row)
            else:
                # Huh, no parent thread..?; create a new one
                # and cache under stripped name so replies will find it
                self._create_thread(row)
                self.thread_cache[stripped_title] = row['id']
        else:
            # At first glance, not a reply; see if another thread
            # already exists with the exact same title:
            thread_id = self.thread_cache.get(row['title'])
            if thread_id:
                # Duplicate; Yahoo or someone lopped off the Re:
                # or it is just a coincidence. Either way, make it
                # a post of an existing thread.
                self._create_post(thread_id, row)
            else:
                self._create_thread(row)
                self.thread_cache[row['title']] = row['id']


    def _create_thread(self, row):
        """
        Create a new thread from the post data by writing a record in the
        thread .csv file and a record in the post file.

        """
        self.thread_writer.writerow((row['id'],
            row['title'].encode('utf-8'),
            row['date'],
            row['author'].encode('utf-8'),
            0))
        self._create_post(row['id'], row)

    def _create_post(self, thread_id, row):
        """
        Create a new post from the post data by writing a record in the
        post .csv file.

        """
        self.post_writer.writerow((row['id'],
            thread_id,
            row['title'].encode('utf-8'),
            row['date'],
            row['author'].encode('utf-8'),
            row['msg'].encode('utf-8'),
            ''))

    def _strip_title(self, title):
        """
        Strip out all the Re: and [SurfGuitar101] stuff to get a bare
        title.

        """
        s = title
        while self.REPLY_RE.match(s):
            s = self.SG101_REPLY_RE.sub('', s).strip()
            s = self.REPLY_RE.sub('', s).strip()

        return s

    @staticmethod
    def get_author(yahoo_id, email):

        def anti_spam(s):
            return s.replace('.', ' dot ').replace('@', ' at ')

        name, addr = parseaddr(email)

        if name == addr:
            name = anti_spam(name)
        else:
            # For some weird reason, sometimes Yahoo (?) put the email address
            # in the name field: "John Doe <doe@example.com" <doe@example.com>"
            name2, addr = parseaddr(name)
            if name2:
                name = name2

        if name and yahoo_id and name != yahoo_id:
            author = "%s (%s)" % (name, yahoo_id)
        elif name:
            author = name
        elif yahoo_id:
            author = yahoo_id
        else:
            author = anti_spam(email)
        return author

###############################################################################

def main(argv=None):
    parser = optparse.OptionParser(usage=USAGE, description=DESCRIPTION)
    parser.set_defaults(
        progress=False,
        host='localhost',
        user='root',
        password='',
        database='sg101_yahoo_group',
    )
    parser.add_option("-s", "--progress", action="store_true",
        help="Output a . after every 100 posts to show progress [default: %default]")
    parser.add_option("-a", "--host",
        help="set MySQL host name [default: %default]"),
    parser.add_option("-u", "--user",
        help="set MySQL user name [default: %default]")
    parser.add_option("-p", "--password",
        help="set MySQL user password [default: %default]"),
    parser.add_option("-d", "--database",
        help="set MySQL database name [default: %default]")
    opts, args = parser.parse_args(args=argv)

    # connect to the legacy database
    try:
        db = MySQLdb.connect(host=opts.host,
                user=opts.user,
                passwd=opts.password,
                db=opts.database,
                use_unicode=True)
    except MySQLdb.DatabaseError, e:
        sys.exit("Can't connect to database: %s" % e)

    converter = ConvertPosts(db, opts.progress)
    converter.process()
    db.close()

###############################################################################

if __name__ == '__main__':
    try:
        main()
    except IOError, ex:
        sys.exit("IO Error: %s" % ex)
    except KeyboardInterrupt:
        sys.exit("Control-C interrupt")
