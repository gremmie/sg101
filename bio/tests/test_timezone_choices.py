"""
Tests that the timezone names the profile form offers can actually be resolved.

The two dropdowns on the profile and calendar forms are not built at runtime.
They are driven by static/js/timezone.js, a generated file holding a frozen list
of zone names, and whatever a user picks there is stored verbatim in
UserProfile.time_zone and handed to ZoneInfo later. So an unresolvable name in
that file does not fail at deploy time -- it fails much later, for one user, as
an exception raised out of a template tag while rendering the forums.

Most of those names are "backward" names such as US/Pacific, which the base
image's own tzdata does not carry at all. They resolve only because the tzdata
package is installed. That is what this test is really guarding: it fails if
tzdata stops being installed, or if a future release of it retires a name this
site has already handed out.
"""
import os
import re
import zoneinfo

from django.conf import settings
from django.test import TestCase


TIMEZONE_JS = os.path.join(settings.PROJECT_PATH, '..', 'static', 'js',
                           'timezone.js')


def offered_timezones():
    """
    Return the set of zone names the timezone.js dropdowns can produce.

    The file declares parallel `areas` and `locations` arrays; a selection is
    one name from each, joined, with spaces mapped back to underscores.
    """
    with open(TIMEZONE_JS) as fp:
        source = fp.read()

    areas = re.search(r'areas:\s*\[(.*?)\]\s*,\s*locations', source, re.S)
    locations = re.search(r'locations:\s*\[(.*?)\]\s*,\s*default_area',
                          source, re.S)
    area_names = re.findall(r"'([^']*)'", areas.group(1))
    location_groups = re.findall(r'\[(.*?)\]', locations.group(1), re.S)

    return set(
        '%s/%s' % (area, location.replace(' ', '_'))
        for area, group in zip(area_names, location_groups)
        for location in re.findall(r"'([^']*)'", group)
    )


class TimezoneChoicesTestCase(TestCase):

    def test_dropdown_offers_zones(self):
        """Guard the parsing above: an empty set would pass every other test."""
        offered = offered_timezones()
        self.assertGreater(len(offered), 300)
        self.assertIn('US/Pacific', offered)

    def test_every_offered_zone_resolves(self):
        unresolvable = []
        for name in sorted(offered_timezones()):
            try:
                zoneinfo.ZoneInfo(name)
            except Exception as ex:
                unresolvable.append('%s (%s)' % (name, type(ex).__name__))

        self.assertEqual(unresolvable, [],
                         "timezone.js offers names that cannot be resolved; "
                         "is the tzdata package still installed?")
