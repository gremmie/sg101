"""
translate_yahoo_group.py - A management command to read the old Yahoo group
posts (in JSON format) and output as a .csv file, suitable for use as an
input to mysqlimport into a database.

How to import:
mysqlimport --fields-optionally-enclosed-by=\" --fields-terminated-by=, --fields-escaped-by="" --lines-terminated-by="\r\n" --user=root --password --local --default-character-set=utf8 sg101_yahoo_group /path/to/post.csv

"""
import csv
import optparse
import datetime
import json
import re
import sys


USAGE = "usage: %prog [options] filename1 filename2 ..."
DESCRIPTION = """\
This command converts the SG101 Yahoo Group posts from JSON and outputs the
data as a .csv file suitable for importing into the new database scheme with
the mysqlimport utility.
"""

DATE_RE = re.compile(r"(\d{4})-(\d{1,2})-(\d{1,2})T(\d{1,2}):(\d{1,2}):(\d{1,2})Z")

# My scraping wasn't perfect and I forgot Yahoo truncated long Yahoo IDs. Provide
# this translation table to fix up the names.

NAME_EXPANSIONS = {
    "atomic_mosqu...": "atomic_mosquitos",
    "balsafliesbe...": "balsafliesbetter",
    "bambinheadli...": "bambinheadlights",
    "batinyourfac...": "batinyourface2002",
    "billyblastof...": "billyblastoff805",
    "bluegrassban...": "bluegrassbanjobabe",
    "bluesbrother...": "bluesbrotherbrian",
    "brother_reyn...": "brother_reynolds",
    "cannistraro_...": "cannistraro_80303",
    "cantemaza_de...": "cantemaza_de_miye",
    "captainraven...": "captainravenwood",
    "captainsprin...": "captainspringfield",
    "colonel_must...": "colonel_mustache",
    "cowboy_playi...": "cowboy_playing_dead",
    "creature_fea...": "creature_features_fan",
    "c_e_l_t_i_c_...": "c_e_l_t_i_c_g_o_t_h",
    "dana_lyn_vin...": "dana_lyn_vincent",
    "destishtarte...": "destishtartenfort",
    "efrem_the_re...": "efrem_the_retarded_rabbit",
    "el_capitan_k...": "el_capitan_kosmo",
    "epiphonecasi...": "epiphonecasino2001",
    "fenderjaguar...": "fenderjaguar1963",
    "fenderplayer...": "fenderplayer52886",
    "fiberglassro...": "fiberglassrocket",
    "formerlyleft...": "formerlylefthanded",
    "guildaristoc...": "guildaristocrat62",
    "guitardo_mon...": "guitardo_montalbone",
    "guitargeekfe...": "guitargeekfestival",
    "harrygpelleg...": "harrygpellegrin2003",
    "iamtheorigin...": "iamtheoriginaltoblave",
    "indiana_surf...": "indiana_surfguitar",
    "invisiblesur...": "invisiblesurfers",
    "jimmywilseyl...": "jimmywilseylives",
    "johnnywrecki...": "johnnywreckingball",
    "killers_from...": "killers_from_space",
    "los_twang_ma...": "los_twang_marvels",
    "midwest_surf...": "midwest_surf_guy",
    "murphy_the_s...": "murphy_the_surfie",
    "national_dis...": "national_disunion421",
    "onlytwothing...": "onlytwothingstodo",
    "photog4surfb...": "photog4surfbands",
    "poseidonsurf...": "poseidonsurfband",
    "reluctantaqu...": "reluctantaquanauts",
    "rich_from_th...": "rich_from_the_balboas",
    "roland_bette...": "roland_bettenville",
    "rvstewartpro...": "rvstewartproductions",
    "screamindeat...": "screamindeathmonkey",
    "sheckysgotre...": "sheckysgotreverb",
    "skatalite_of...": "skatalite_of_love",
    "slippy_the_b...": "slippy_the_backflipping_frog",
    "somethingabo...": "somethingaboutwendy",
    "storm_static...": "storm_static_sleep",
    "supertwangre...": "supertwangreverb",
    "surfalicious...": "surfaliciousdude1",
    "surf_guitar_...": "surf_guitar_lizzy",
    "taylorsnyder...": "taylorsnyderband",
    "teenageflami...": "teenageflamingovandals",
    "thecaveofthe...": "thecaveofthedead",
    "tikitakitiki...": "tikitakitikitakitak",
    "troublewitht...": "troublewithtreble",
    "tumamaentang...": "tumamaentangadeluchador",
    "warped_skate...": "warped_skater_182",
    "weird_jack_s...": "weird_jack_stinson",
    "whatever5050...": "whatever50505050",
    "windanseabea...": "windanseabeachboy",
    "Wookiee_Smug...": "Wookiee_Smuggler_Drayyken",
}

def convert_date(s):
    """
    Converts the timestamp string of the form "yyyy-mm-ddTHH:MM:SSZ" into a
    datetime object.
    """
    m = DATE_RE.match(s)
    assert m is not None

    parts = [int(part) for part in m.groups()]
    return datetime.datetime(year=parts[0], month=parts[1], day=parts[2],
            hour=parts[3], minute=parts[4], second=parts[5])


def process_line(line, writer):
    """
    Process one line from the JSON file: create a CSV line for the post.

    """
    # Remove trailing newline
    line = line.strip()

    # The JSON files consist of one large array of dicts, one dict per line.
    # The first line in the file thus has an opening '[' we need to get rid of.
    # The last char in each line is either a ',' or a ']', so we need to 
    # lose the last char as well. That should leave us with just a dict.
    if line.startswith('['):
        line = line[1:]
    line = line[:-1].strip()
    parts = json.loads(line)

    # Convert the post date; for some strange reason, some dates were not available
    # and the date value will be an empty string. In these cases we'll output a NULL.
    post_date = parts['date']
    if not post_date:
        post_date = 'NULL'
    else:
        post_date = str(convert_date(post_date))

    name = parts['name']
    name = NAME_EXPANSIONS.get(name, name)

    # write the parts as CSV
    writer.writerow((parts['msg_id'],
            parts['title'].encode('utf-8'),
            post_date,
            name.encode('utf-8'),
            parts['email'].encode('utf-8'),
            parts['msg'].encode('utf-8')))


def main(argv=None):

    parser = optparse.OptionParser(usage=USAGE, description=DESCRIPTION)
    parser.set_defaults(
        progress=False,
        output='post.csv',
    )
    parser.add_option("-p", "--progress", action="store_true",
        help="Output a . after every 100 posts to show progress [default: %default]")
    parser.add_option("-o", "--output",
        help="Name of the output file [default: %default]")

    opts, args = parser.parse_args(args=argv)

    with open(opts.output, "wb") as out_file:
        writer = csv.writer(out_file)

        for filename in args:
            print "Processing " + filename
            with open(filename, "r") as in_file:
                posts = 0
                for line in in_file:
                    process_line(line, writer)
                    posts += 1
                    if opts.progress and posts % 100 == 0:
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
