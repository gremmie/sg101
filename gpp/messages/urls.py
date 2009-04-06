"""urls for the Messages application"""
from django.conf.urls.defaults import *

urlpatterns = patterns('messages.views',
    url(r'^inbox/$', 'inbox', name='messages-inbox'),
    url(r'^outbox/$', 'outbox', name='messages-outbox'),
    url(r'^trash/$', 'trash', name='messages-trash'),
    url(r'^view/(\d+)/$', 'view', name='messages-view'),
    url(r'^reply/(\d+)/$', 'reply', name='messages-reply'),
    url(r'^compose/$', 'compose', name='messages-compose'),
    url(r'^compose/(\w+)/$', 'compose', name='messages-compose_to'),
    url(r'^delete/$', 'delete_bulk', name='messages-delete_bulk'),
    url(r'^delete/(\d+)/$', 'delete', name='messages-delete'),
    url(r'^undelete/$', 'undelete_bulk', name='messages-undelete_bulk'),
    url(r'^undelete/(\d+)/$', 'undelete', name='messages-undelete'),
    url(r'^options/$', 'options', name='messages-options'),
    url(r'^ajax/users/$', 'ajax_users', name='messages-ajax_users'),
)

urlpatterns += patterns('django.views.generic.simple',
    (r'^$', 'redirect_to', {'url': 'inbox/'}),
)


# vim: ts=4 sw=4
