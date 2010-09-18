"""
This program generates the data used by the timezone.js Javascript.
This data is used to create the 2 dropdown select boxes for timezones.
"""
import pytz
from pprint import pprint

def format_locations(locs):
    ss = ["[%s]" % ", ".join(["'%s'" % l for l in loc]) for loc in locs]
    return "%s" % ",\n".join(ss)

# get a list of areas

zones = [z.split('/') for z in pytz.common_timezones]
areas = set([zone[0] for zone in zones if len(zone) > 1])
areas = list(areas)
areas.sort()

locations = dict([(area, []) for area in areas])

#pprint(locations)

for zone in pytz.common_timezones:
    if zone.count('/') == 0:
        continue
    area, loc = zone.split('/', 1)
    if area in locations:
        locations[area].append(loc.replace('_', ' '))

#pprint(locations)

for area in locations.iterkeys():
    locations[area].sort()

locs = []
for area in areas:
    locs.append(locations[area])

#pprint(locs)

default_area = areas.index('US')
default_location = locs[default_area].index('Pacific')

print """\
var gcalTzInfo = {
    areas: [%s],
    locations: [%s],
    default_area: %s,
    default_location: %s
};
""" % (", ".join(["'%s'" % area for area in areas]), 
        format_locations(locs),
        default_area,
        default_location,
        )
