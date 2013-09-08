"""URLs for the user_photos application."""
from django.conf.urls import patterns, url

urlpatterns = patterns('user_photos.views',
    url(r'^upload/$', 'upload', name='user_photos-upload'),
)
