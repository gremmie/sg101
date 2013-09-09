"""URLs for the user_photos application."""
from django.conf.urls import patterns, url
from django.views.generic import DetailView

from user_photos.models import Photo


urlpatterns = patterns('user_photos.views',
    url(r'^upload/$', 'upload', name='user_photos-upload'),
    url(r'^photo/(?P<pk>\d+)/$',
        DetailView.as_view(model=Photo),
        name='user_photos-detail')
)
