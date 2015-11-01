"""
This file contains the automatic admin site definitions for the gcalendar application.

"""
from django.conf import settings
from django.conf.urls import patterns, url
from django.contrib import admin
from django.contrib import messages
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render

from gcalendar.models import Event
from gcalendar.calendar import Calendar, CalendarError
from gcalendar import oauth

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
        my_urls = patterns('',
            url(r'^google_sync/$',
                self.admin_site.admin_view(self.google_sync),
                name="gcalendar-google_sync"),
            url(r'^authorize/$',
                self.admin_site.admin_view(self.authorize),
                name="gcalendar-authorize"),
             url(r'^auth_return/$',
                self.admin_site.admin_view(self.auth_return),
                name="gcalendar-auth_return"),
        )
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

        # Check status of credentials file
        cred_status = oauth.check_credentials_status()

        msgs = []
        err_msg = ''
        if request.method == 'POST':
            credentials = oauth.get_credentials()
            if credentials:
                try:
                    cal = Calendar(calendar_id=settings.GCAL_CALENDAR_ID,
                            credentials=credentials)
                    cal.sync_events(events)
                except CalendarError, e:
                    err_msg = str(e)
                    events = Event.pending_events.all()
                else:
                    msgs.append('All events processed successfully.')
                    events = Event.objects.none()
            else:
                self.message_user(request, "Invalid or missing credentials",
                        level=messages.ERROR)

        return render(request, 'gcalendar/google_sync.html', {
            'current_app': self.admin_site.name,
            'cred_status': cred_status,
            'messages': msgs,
            'err_msg': err_msg,
            'events': events,
            })

    def authorize(self, request):
        """
        This view generates the authorization URL and redirects the user to it.
        """
        site = Site.objects.get_current()
        callback_url = '%s://%s%s' % (
                settings.SITE_SCHEME,
                site.domain,
                reverse('admin:gcalendar-auth_return'))
        auth_url = oauth.get_auth_url(callback_url)
        return HttpResponseRedirect(auth_url)

    def auth_return(self, request):
        """
        This view is called by Google after the user has authorized us access to
        their data. We call into the oauth module to process the authorization
        code and exchange it for tokens.
        """
        try:
            oauth.auth_return(request)
        except oauth.OAuthError as e:
            self.message_user(request, str(e), level=messages.ERROR)

        return HttpResponseRedirect(reverse('admin:gcalendar-google_sync'))


admin.site.register(Event, EventAdmin)
