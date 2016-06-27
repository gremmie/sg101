"""
URLs for the gcalendar application.
"""
from django.conf.urls import url

import gcalendar.views


urlpatterns = [
    url(r'^$', gcalendar.views.index, name='gcalendar-index'),
    url(r'^add/$', gcalendar.views.add_event, name='gcalendar-add'),
    url(r'^change/$', gcalendar.views.edit_events, name='gcalendar-edit_events'),
    url(r'^change/(\d+)/$', gcalendar.views.edit_event, name='gcalendar-edit_event'),
    url(r'^delete/$', gcalendar.views.delete_event, name='gcalendar-delete'),
]
