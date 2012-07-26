"""
Application to read the ISO-3166 country data and output a JSON datastructure
for use in the SG101 code. We also print a report of any missing country
icons. If we don't have an icon for a country, we don't include it in our JSON
data.

"""
import argparse
import json
import os.path
from xml.etree.ElementTree import ElementTree


def main():
    parser = argparse.ArgumentParser(description=("Transform Debian's ISO-3166 "
        "data into JSON for use on SG101"))
    parser.add_argument('--xml', '-x', required=True, help='path to XML file')
    parser.add_argument('--icon-dir', '-i', required=True,
            help='path to icon directory')

    args = parser.parse_args()

    xml_file = os.path.expanduser(args.xml)
    icon_dir = os.path.expanduser(args.icon_dir)

    with open(xml_file, 'r') as fp:
        et = ElementTree(file=fp)

    country_data = {}
    for node in et.iterfind('iso_3166_entry'):
        code = node.get('alpha_2_code').lower()
        name = node.get('common_name', node.get('name'))

        # see if we have an icon for this country

        if not os.path.exists(os.path.join(icon_dir, '%s.png' % code)):
            print "Could not find icon for %s (%s)" % (name, code)
        else:
            country_data[code] = name

    s = json.dumps(country_data, indent=4, sort_keys=True, ensure_ascii=False)
    print s.encode('utf-8')


if __name__ == '__main__':
    main()
