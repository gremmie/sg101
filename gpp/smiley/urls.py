"""
Urls for the Smiley application.
"""

from django.conf.urls import patterns, url

urlpatterns = patterns('smiley.views',
    url(r'^farm/$', 'farm', name='smiley-farm'),
    url(r'^farm/extra/$', 'farm', kwargs={'extra': True}, name='smiley-farm_extra'),
)
