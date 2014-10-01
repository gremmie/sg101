"""Admin definitions for the bandmap application.

"""
import datetime
import json
import urllib
import urllib2

from django.contrib import admin
import django.contrib.messages as messages

from bandmap.models import BandEntry
import bio.badges


class BandEntryAdmin(admin.ModelAdmin):
    list_display = ['name', 'date_submitted', 'location', 'lat', 'lon',
            'is_active', 'is_approved']
    date_hierarchy = 'date_submitted'
    list_filter = ['date_submitted', 'is_active', 'is_approved']
    readonly_fields = ['lat', 'lon']
    search_fields = ['name', 'location', 'note']
    raw_id_fields = ['user']
    actions = ['update_location', 'approve_bands']

    def approve_bands(self, request, qs):
        """This admin action awards a map pin to the user who added the band.
        The band is then published and will be available for display on the map.

        """
        count = qs.count()
        now = datetime.datetime.now()
        for band in qs:
            if not band.is_approved:
                if band.date_approved is None:
                    bio.badges.award_badge(bio.badges.MAP_PIN, band.user)
                band.date_approved = now
                band.is_approved = True
                band.save()

        self.message_user(request, "%d band(s) approved." % count)

    approve_bands.short_description = "Approve selected band map entries"

    def update_location(self, request, qs):
        """Admin action to refresh the lat/lon fields after updating the
        location field. Queries the Google Maps HTTP server-side API for the
        data.

        """
        base_url = "http://maps.googleapis.com/maps/api/geocode/json?address=%s"
        ok_cnt = 0
        for band in qs:
            url = base_url % urllib.quote_plus(band.location)
            try:
                response = urllib2.urlopen(url)
            except urllib2.URLError as ex:
                self.message_user(request, 'Error processing {}: {}'.format(
                    band.name, ex), level=messages.ERROR)
                continue

            code = response.getcode()
            if code == 200:
                result = json.loads(response.read())
                try:
                    loc = result['results'][0]['geometry']['location']
                    band.lat = loc['lat']
                    band.lon = loc['lng']
                except (KeyError, IndexError) as ex:
                    self.message_user(request, 'Unexpected response for {}'.format(
                        band.name), level=messages.ERROR)
                else:
                    band.save()
                    ok_cnt += 1
            else:
                msg = "Error response ({}) for band {}".format(code, band.name)
                self.message_user(request, msg, level=messages.ERROR)

        if ok_cnt > 0:
            msg = '{} band location(s) successfully updated'.format(ok_cnt)
            self.message_user(request, msg)

    update_location.short_description = "Update lat/lon for selected band map entries"


admin.site.register(BandEntry, BandEntryAdmin)
