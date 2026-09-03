"""
This file contains the automatic admin site definitions for the gcalendar application.

"""
from django.conf import settings
from django.contrib import admin
from django.urls import path
from django.shortcuts import render

from gcalendar.models import Event
from gcalendar.calendar import Calendar, CalendarError

import bio.badges


class EventAdmin(admin.ModelAdmin):
    list_display = ['what', 'user', 'start_date', 'where', 'date_submitted',
            'status', 'is_approved', 'google_html']
    list_filter = ['start_date', 'status']
    date_hierarchy = 'start_date'
    search_fields = ['what', 'where', 'description']
    raw_id_fields = ['user']
    exclude = ['html', 'google_id', 'google_url']
    save_on_top = True
    actions = ['approve_events']

    pending_states = {
        Event.NEW: Event.NEW_APRV,
        Event.EDIT_REQ: Event.EDIT_APRV,
        Event.DEL_REQ: Event.DEL_APRV,
    }

    def get_urls(self):
        urls = super(EventAdmin, self).get_urls()
        my_urls = [
            path('google_sync/',
                self.admin_site.admin_view(self.google_sync),
                name="gcalendar-google_sync"),
        ]
        return my_urls + urls

    def approve_events(self, request, qs):
        """
        Ratchets the selected events forward to the approved state.
        Ignores events that aren't in the proper state.
        """
        count = 0
        for event in qs:
            if event.status in self.pending_states:
                event.status = self.pending_states[event.status]
                event.save()
                count += 1

                if event.status == Event.NEW_APRV:
                    bio.badges.award_badge(bio.badges.CALENDAR_PIN, event.user)

        msg = "1 event was" if count == 1 else "%d events were" % count
        msg += " approved."
        self.message_user(request, msg)

    approve_events.short_description = "Approve selected events"

    def google_sync(self, request):
        """
        View to synchronize approved event changes with Google calendar.

        """
        # Get pending events
        events = Event.pending_events.all()

        msgs = []
        err_msg = ''
        if request.method == 'POST':
            try:
                cal = Calendar(calendar_id=settings.GCAL_CALENDAR_ID,
                        credentials_path=settings.GCAL_CREDENTIALS_PATH)
                cal.sync_events(events)
            except CalendarError as e:
                err_msg = str(e)
                events = Event.pending_events.all()
            else:
                msgs.append('All events processed successfully.')
                events = Event.objects.none()

        return render(request, 'gcalendar/google_sync.html', {
            'current_app': self.admin_site.name,
            'messages': msgs,
            'err_msg': err_msg,
            'events': events,
            })


admin.site.register(Event, EventAdmin)
