"""
Admin definitions for the member map application models.
"""

from django.contrib import admin

from membermap.models import MapEntry

class MapEntryAdmin(admin.ModelAdmin):
   exclude = ('html', )
   list_display = ('user', 'location', 'lat', 'lon', 'date_updated')
   list_filter = ('date_updated', )
   date_hierarchy = 'date_updated'
   ordering = ('-date_updated', )
   search_fields = ('user', 'location', 'message')
   raw_id_fields = ('user', )
   
admin.site.register(MapEntry, MapEntryAdmin)
