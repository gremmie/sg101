"""
URLs for the gcalendar application.
"""
from django.conf.urls import patterns, url

urlpatterns = patterns('gcalendar.views',
    url(r'^$', 'index', name='gcalendar-index'),
    url(r'^add/$', 'add_event', name='gcalendar-add'),
    url(r'^change/$', 'edit_events', name='gcalendar-edit_events'),
    url(r'^change/(\d+)/$', 'edit_event', name='gcalendar-edit_event'),
    url(r'^delete/$', 'delete_event', name='gcalendar-delete'),
    url(r'^thanks/add/$', 'add_thanks', name='gcalendar-add_thanks'),
    url(r'^thanks/change/$', 'edit_thanks', name='gcalendar-edit_thanks'),
)
