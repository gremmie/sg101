"""
Urls for the Smiley application.
"""
from django.urls import path

import smiley.views


urlpatterns = [
    path('farm/', smiley.views.farm, name='smiley-farm'),
    path('farm/extra/', smiley.views.farm, kwargs={'extra': True}, name='smiley-farm_extra'),
]
