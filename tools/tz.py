"""
This program generates the data used by the timezone.js Javascript.
This data is used to create the 2 dropdown select boxes for timezones.

Run it from the repo root and redirect the output over the static file:

    python tools/tz.py > static/js/timezone.js

Regenerating is a user-facing change rather than a refresh: the committed file
was generated from pytz's common_timezones back in 2010, and every value in a
UserProfile.time_zone column was chosen from that list. zoneinfo is built to a
different rule -- every zone the system carries, including "backward" aliases,
rather than a curated list of zones in current use.

Measured 2026-08-09: regenerating would be purely additive, offering 553 zones
across 16 areas against the committed file's 401 across 11. It adds 152 and
drops none, so no stored value would stop being offered. The open question is
whether a longer list is an improvement for people picking from it, not whether
it is safe.
"""
import zoneinfo


def format_locations(locs):
    ss = ["[%s]" % ", ".join(["'%s'" % l for l in loc]) for loc in locs]
    return "%s" % ",\n".join(ss)


# get a list of areas
zone_names = sorted(zoneinfo.available_timezones())

zones = [z.split('/') for z in zone_names]
areas = sorted({zone[0] for zone in zones if len(zone) > 1})

locations = {area: [] for area in areas}

for zone in zone_names:
    if zone.count('/') == 0:
        continue
    area, loc = zone.split('/', 1)
    if area in locations:
        locations[area].append(loc.replace('_', ' '))

for area in locations:
    locations[area].sort()

locs = [locations[area] for area in areas]

default_area = areas.index('US')
default_location = locs[default_area].index('Pacific')

print("""\
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
        ))
