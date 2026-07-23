"""
Urls for the Shoutbox application.
"""

from django.urls import path

import shoutbox.views


urlpatterns = [
    path('delete/', shoutbox.views.delete, name='shoutbox-delete'),
    path('edit/', shoutbox.views.edit, name='shoutbox-edit'),
    path('flag/', shoutbox.views.flag, name='shoutbox-flag'),
    path('shout/', shoutbox.views.shout, name='shoutbox-shout'),
    path('text/', shoutbox.views.text, name='shoutbox-text'),
    path('view/<int:id>/', shoutbox.views.view_shout, name='shoutbox-view'),
    path('view/history/', shoutbox.views.view_history, name='shoutbox-history'),
]
