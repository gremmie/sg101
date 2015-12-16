"""urls for the Messages application"""
from django.conf.urls import url
from django.views.generic.base import RedirectView

import messages.views


urlpatterns = [
    url(r'^$',
        RedirectView.as_view(permanent=True, url='/messages/inbox/'),
        name='messages-index'),
    url(r'^inbox/$',
        messages.views.inbox,
        name='messages-inbox'),
    url(r'^compose/$',
        messages.views.compose,
        name='messages-compose'),
    url(r'^outbox/$',
        messages.views.outbox,
        name='messages-outbox'),
    url(r'^trash/$',
        messages.views.trash,
        name='messages-trash'),
    url(r'^options/$',
        messages.views.options,
        name='messages-options'),
    url(r'^bulk/$',
        messages.views.bulk,
        name='messages-bulk'),
    url(r'^undelete/$',
        messages.views.undelete,
        name='messages-undelete'),
    url(r'^view/(\d+)/$',
        messages.views.view,
        name='messages-view'),
    url(r'^report/(\d+)/$',
        messages.views.report,
        name='messages-report'),
]
