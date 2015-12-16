"""
Urls for the Smiley application.
"""
from django.conf.urls import url

import smiley.views


urlpatterns = [
    url(r'^farm/$', smiley.views.farm, name='smiley-farm'),
    url(r'^farm/extra/$', smiley.views.farm, kwargs={'extra': True}, name='smiley-farm_extra'),
]
