"""urls for the Messages application"""
from django.urls import path
from django.views.generic.base import RedirectView

import messages.views


urlpatterns = [
    path('',
        RedirectView.as_view(permanent=True, url='/messages/inbox/'),
        name='messages-index'),
    path('inbox/',
        messages.views.inbox,
        name='messages-inbox'),
    path('compose/',
        messages.views.compose,
        name='messages-compose'),
    path('outbox/',
        messages.views.outbox,
        name='messages-outbox'),
    path('trash/',
        messages.views.trash,
        name='messages-trash'),
    path('options/',
        messages.views.options,
        name='messages-options'),
    path('bulk/',
        messages.views.bulk,
        name='messages-bulk'),
    path('undelete/',
        messages.views.undelete,
        name='messages-undelete'),
    path('view/<int:msg_id>/',
        messages.views.view,
        name='messages-view'),
    path('report/<int:msg_id>/',
        messages.views.report,
        name='messages-report'),
]
