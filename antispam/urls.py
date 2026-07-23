"""URLs for the antispam application."""
from django.urls import path

import antispam.views


urlpatterns = [
    path('suspended/', antispam.views.suspended, name='antispam-suspended'),
]
