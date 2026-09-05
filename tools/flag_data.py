"""
Application to read the ISO-3166 country data and output a JSON datastructure
for use in the SG101 code. We also print a report of any missing country
icons. If we don't have an icon for a country, we don't include it in our JSON
data.

Reads Debian's `iso-codes` JSON, usually /usr/share/iso-codes/json/iso_3166-1.json.
The iso_3166.xml this used to parse is still installed, but it is a symlink to
iso_3166-1.xml whose own header reads "THIS FILE IS DEPRECATED, PLEASE USE THE
JSON DATA INSTEAD". Both carry the same 249 countries; only the attribute names
differ (`alpha_2_code` in the XML, `alpha_2` in the JSON).

"""
import argparse
import json
import os.path
import sys


def main():
    parser = argparse.ArgumentParser(description=("Transform Debian's ISO-3166 "
        "data into JSON for use on SG101"))
    parser.add_argument('--json', '-j', required=True,
            help='path to iso_3166-1.json')
    parser.add_argument('--icon-dir', '-i', required=True,
            help='path to icon directory')

    args = parser.parse_args()

    json_file = os.path.expanduser(args.json)
    icon_dir = os.path.expanduser(args.icon_dir)

    with open(json_file, 'r', encoding='utf-8') as fp:
        entries = json.load(fp)['3166-1']

    country_data = {}
    for entry in entries:
        code = entry['alpha_2'].lower()
        name = entry.get('common_name', entry['name'])

        # see if we have an icon for this country

        if not os.path.exists(os.path.join(icon_dir, '%s.png' % code)):
            sys.stderr.write("Could not find icon for %s (%s)\n" % (name, code))
        else:
            country_data[code] = name

    s = json.dumps(country_data, indent=4, sort_keys=True, ensure_ascii=False)
    print(s)


if __name__ == '__main__':
    main()
