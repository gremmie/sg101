"""
Url patterns for the phantombrigade application.

"""
from django.conf.urls import patterns, url


urlpatterns = patterns('phantombrigade.views',
   url(r'^ts3/$', 'ts3_query', name='phantombrigade-ts3'),
)
