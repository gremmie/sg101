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

import gdata.client

from gcalendar.models import Event, AccessToken
from gcalendar.calendar import Calendar, CalendarError
from gcalendar import oauth

import bio.badges


SCOPES = ['https://www.google.com/calendar/feeds/']


class EventAdmin(admin.ModelAdmin):
    list_display = ('what', 'user', 'start_date', 'where', 'date_submitted',
            'status', 'is_approved', 'google_html')
    list_filter = ('start_date', 'status')
    date_hierarchy = 'start_date'
    search_fields = ('what', 'where', 'description')
    raw_id_fields = ('user', )
    exclude = ('html', 'google_id', 'google_url')
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
                self.admin_site.admin_view(self.google_sync),
                name="gcalendar-google_sync"),
            url(r'^fetch_auth/$',
                self.admin_site.admin_view(self.fetch_auth),
                name="gcalendar-fetch_auth"),
             url(r'^get_access_token/$',
                self.admin_site.admin_view(self.get_access_token),
                name="gcalendar-get_access_token"),
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

        # Attempt to get saved access token to the Google calendar
        access_token = AccessToken.objects.get_token().access_token()

        messages = []
        err_msg = ''
        if request.method == 'POST':
            if access_token:
                try:
                    cal = Calendar(source=oauth.USER_AGENT,
                            calendar_id=settings.GCAL_CALENDAR_ID,
                            access_token=access_token)
                    cal.sync_events(events)
                except CalendarError, e:
                    err_msg = e.msg
                    events = Event.pending_events.all()
                else:
                    messages.append('All events processed successfully.')
                    events = Event.objects.none()

        return render(request, 'gcalendar/google_sync.html', {
            'current_app': self.admin_site.name,
            'access_token': access_token,
            'messages': messages,
            'err_msg': err_msg,
            'events': events,
            })

    def fetch_auth(self, request):
        """
        This view fetches a request token and then redirects the user to
        authorize it.

        """
        site = Site.objects.get_current()
        callback_url = 'http://%s%s' % (site.domain,
                reverse('admin:gcalendar-get_access_token'))
        try:
            auth_url = oauth.fetch_auth(request, SCOPES, callback_url)
        except gdata.client.Error, e:
            messages.error(request, str(e))
            return HttpResponseRedirect(reverse('admin:gcalendar-google_sync'))
        else:
            return HttpResponseRedirect(auth_url)

    def get_access_token(self, request):
        """
        This view is called by Google after the user has authorized us access to
        their data. We call into the oauth module to upgrade the oauth token to
        an access token. We then save the access token in the database and
        redirect back to our admin Google sync view.

        """
        try:
            access_token = oauth.get_access_token(request)
        except gdata.client.Error, e:
            messages.error(request, str(e))
        else:
            token = AccessToken.objects.get_token()
            token.update(access_token)
            token.save()

        return HttpResponseRedirect(reverse('admin:gcalendar-google_sync'))


admin.site.register(Event, EventAdmin)
admin.site.register(AccessToken)
