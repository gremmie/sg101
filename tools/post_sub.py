"""
This script reads a .csv dump of the forums post table. It writes a new file,
performing a search and replace over a given field.

The output file can be imported into MySQL with:

LOAD DATA LOCAL INFILE 'forums_post.csv' REPLACE INTO TABLE forums_post
CHARACTER SET utf8
FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"' ESCAPED BY ''
LINES TERMINATED BY '\r\n';
SHOW WARNINGS;

"""
import csv
import re
import optparse
import sys


USAGE = "usage: %prog [options] infile outfile"
DESCRIPTION = """\
Performs a search and replace on a field in a forums post .csv file.
"""

POST_FIELDS = ('id', 'topic_id', 'user_id', 'creation_date', 'update_date',
        'body', 'html', 'user_ip')


def main(argv=None):
    parser = optparse.OptionParser(usage=USAGE, description=DESCRIPTION)
    parser.set_defaults(
        progress=False,
        field='body',
    )
    parser.add_option("-p", "--progress", action="store_true",
        help="Output a . after every 100 posts to show progress [default: %default]")
    parser.add_option("-f", "--field",
        help="Name of the field to search [default: %default]")
    parser.add_option("-s", "--search", help="The search pattern")
    parser.add_option("-r", "--replace", help="The replacement text")

    opts, args = parser.parse_args(args=argv)

    if len(args) != 2:
        sys.exit("Please supply input and output file arguments.")

    if opts.search is None:
        sys.exit("Please specify a search pattern.")
    search_re = re.compile(opts.search)

    if opts.replace is None:
        sys.exit("Please specify replacement text.")

    with open(args[0], "rb") as infile:
        reader = csv.DictReader(infile)
        if opts.field not in reader.fieldnames:
            sys.exit("Error, invalid field option: %s" % opts.field)

        with open(args[1], "wb") as outfile:
            writer = csv.DictWriter(outfile, POST_FIELDS)

            n = 0
            for row in reader:
                row[opts.field] = search_re.sub(opts.replace, row[opts.field])
                writer.writerow(row)

                if n % 100 == 0:
                    sys.stdout.write('.')
                    sys.stdout.flush()

            print

if __name__ == '__main__':
    try:
        main()
    except IOError, ex:
        sys.exit("IO Error: %s" % ex)
    except KeyboardInterrupt:
        sys.exit("Control-C interrupt")
