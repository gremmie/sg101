"""
filter_posts.py - A script to filter out posts that have no parent topic in the
new database. 

"""
import csv
import optparse
import sys


USAGE = "usage: %prog [options]"
DESCRIPTION = """Filters out posts that have no parent topic."""


def main(argv=None):

    parser = optparse.OptionParser(usage=USAGE, description=DESCRIPTION)
    parser.set_defaults(
        topic_file='forums_topic.csv',
        post_file='forums_post.csv',
        output_file='forums_post_filtered.csv',
    )
    parser.add_option("-s", "--progress", action="store_true",
        help="Output a . after every 100 posts to show progress [default: %default]")
    parser.add_option("-t", "--topic-file",
        help="Name of the topics csv file [default: %default]")
    parser.add_option("-p", "--post-file",
        help="Name of the posts csv file [default: %default]")
    parser.add_option("-o", "--output-file",
        help="Name of the output posts csv file [default: %default]")

    opts, args = parser.parse_args(args=argv)

    topics = set()
    with open(opts.topic_file, "rb") as topic_file:
        reader = csv.reader(topic_file)
        for row in reader:
            topics.add(int(row[0]))

    with open(opts.post_file, "rb") as post_file:
        reader = csv.reader(post_file)
        # skip first row
        print reader.next()
        with open(opts.output_file, "wb") as output_file:
            writer = csv.writer(output_file)
            for row in reader:
                topic = int(row[1])
                if topic in topics:
                    writer.writerow(row)
                    

if __name__ == '__main__':
    try:
        main()
    except IOError, ex:
        sys.exit("IO Error: %s" % ex)
    except KeyboardInterrupt:
        sys.exit("Control-C interrupt")
