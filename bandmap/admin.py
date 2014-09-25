"""Admin definitions for the bandmap application.

"""
import datetime

from django.contrib import admin

from bandmap.models import BandEntry
import bio.badges


class BandEntryAdmin(admin.ModelAdmin):
    list_display = ['name', 'date_submitted', 'date_approved', 'is_active',
            'is_approved']
    date_hierarchy = 'date_submitted'
    list_filter = ['date_submitted', 'is_active', 'is_approved']
    readonly_fields = ['lat', 'lon']
    search_fields = ['name', 'location', 'note']
    raw_id_fields = ['user']
    actions = ['approve_bands']

    def approve_bands(self, request, qs):
        """This admin action awards a map pin to the user who added the band.
        The band is then published and will be available for display on the map.

        """
        count = qs.count()
        now = datetime.datetime.now()
        for band in qs:
            bio.badges.award_badge(bio.badges.MAP_PIN, band.user)
            band.date_approved = now
            band.is_approved = True
            band.save()

        self.message_user(request, "%d band(s) approved." % count)

    approve_bands.short_description = "Approve selected band map entries"


admin.site.register(BandEntry, BandEntryAdmin)
