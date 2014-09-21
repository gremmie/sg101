"""Admin definitions for the bandmap application.

"""
from django.contrib import admin

from bandmap.models import BandEntry


class BandEntryAdmin(admin.ModelAdmin):
    list_display = ['name', 'date_submitted', 'date_approved', 'is_active',
            'is_approved']
    date_hierarchy = 'date_submitted'
    list_filter = ['date_submitted', 'is_active', 'is_approved']
    readonly_fields = ['lat', 'lon']
    search_fields = ['name', 'location', 'note']
    raw_id_fields = ['user']

admin.site.register(BandEntry, BandEntryAdmin)
