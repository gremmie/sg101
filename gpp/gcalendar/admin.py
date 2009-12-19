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
    date_hierarchy = 'start_date'
    search_fields = ('what', 'where', 'description')
    raw_id_fields = ('user', )
    exclude = ('html', 'google_id')
    save_on_top = True
    actions = ('approve_events', )

    pending_states = {
        Event.NEW: Event.NEW_APRV,
        Event.EDIT_REQ: Event.EDIT_APRV,
        Event.DEL_REQ: Event.DEL_APRV,
    }

    def get_urls(self):
        urls = super(EventAdmin, self).get_urls()
        my_urls = patterns('',
            url(r'^google_sync/$', 
                self.admin_site.admin_view(google_sync), 
                name="gcalendar-google_sync")
        )
        return my_urls + urls

    def approve_events(self, request, qs):
        """
        Ratchets the selected events forward to the approved state.
        Ignores events that aren't in the proper state.
        """
        for event in qs:
            count = 0
            if event.status in self.pending_states:
                event.status = self.pending_states[event.status]
                event.save()
                count += 1

        msg = "1 event was" if count == 1 else "%d events were" % count
        msg += " approved."
        self.message_user(request, msg)

    approve_events.short_description = "Approve selected events"


admin.site.register(Event, EventAdmin)

