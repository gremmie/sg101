"""
This file contains the automatic admin site definitions for the gcalendar application.

"""
from django.conf import settings
from django.conf.urls.defaults import *
from django.contrib import admin
from django.contrib import messages
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext

import gdata.client

from gcalendar.models import Event, AccessToken
from gcalendar.forms import PasswordForm
from gcalendar.calendar import Calendar
from gcalendar.calendar import CalendarError
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
        """View to synchronize approved event changes with Google calendar."""
        events = Event.pending_events.all()
        messages = []
        err_msg = ''
        if request.method == 'POST':
            form = PasswordForm(request.POST)
            if form.is_valid():
                try:
                    cal = Calendar(settings.GCAL_EMAIL,
                            form.cleaned_data['password'],
                            settings.GCAL_CALENDAR_ID)
                    cal.sync_events(events)
                except CalendarError, e:
                    err_msg = e.msg
                    events = Event.pending_events.all()
                    form = PasswordForm()
                else:
                    messages.append('All events processed successfully.')
                    events = Event.objects.none()
                    form = PasswordForm()

        else:
            form = PasswordForm()

        return render_to_response('gcalendar/google_sync.html', {
            'current_app': self.admin_site.name,
            'messages': messages,
            'err_msg': err_msg,
            'events': events,
            'form': form,
            },
            context_instance=RequestContext(request))

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
            try:
                token = AccessToken.objects.get(id=1)
            except AccessToken.DoesNotExist:
                token = AccessToken()

            token.token = gdata.gauth.TokenToBlob(access_token)
            token.auth_date = datetime.datetime.now()
            token.save()

        return HttpResponseRedirect(reverse('admin:gcalendar-google_sync'))


admin.site.register(Event, EventAdmin)
admin.site.register(AccessToken)
