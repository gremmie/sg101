"""
This file contains the automatic admin site definitions for the gcalendar application.
"""
from django.contrib import admin
from django.http import HttpResponse
from django.conf.urls.defaults import *

from gcalendar.models import Event
from gcalendar.admin_views import google_sync


class EventAdmin(admin.ModelAdmin):
    list_display = ('what', 'user', 'start_date', 'where', 'date_submitted',
            'status', 'is_approved')
    list_filter = ('start_date', 'status')
    search_fields = ('what', 'where', 'description')
    raw_id_fields = ('user', )
    exclude = ('html', 'google_id')
    save_on_top = True

    def get_urls(self):
        urls = super(EventAdmin, self).get_urls()
        my_urls = patterns('',
            url(r'^google_sync/$', 
                self.admin_site.admin_view(google_sync), 
                name="gcalendar-google_sync")
        )
        return my_urls + urls


admin.site.register(Event, EventAdmin)

# vim: ts=4 sw=4
