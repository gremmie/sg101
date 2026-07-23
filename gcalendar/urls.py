"""
URLs for the gcalendar application.
"""
from django.urls import path

import gcalendar.views


urlpatterns = [
    path('', gcalendar.views.index, name='gcalendar-index'),
    path('add/', gcalendar.views.add_event, name='gcalendar-add'),
    path('change/', gcalendar.views.edit_events, name='gcalendar-edit_events'),
    path('change/<int:event_id>/', gcalendar.views.edit_event, name='gcalendar-edit_event'),
    path('delete/', gcalendar.views.delete_event, name='gcalendar-delete'),
]
