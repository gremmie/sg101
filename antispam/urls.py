"""URLs for the antispam application."""
from django.conf.urls import url

import antispam.views


urlpatterns = [
    url(r'^suspended/$', antispam.views.suspended, name='antispam-suspended'),
]
