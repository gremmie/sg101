"""URLs for the user_photos application."""
from django.conf.urls import patterns, url
from django.views.generic import DetailView

from user_photos.models import Photo
from user_photos.views import GalleryView


urlpatterns = patterns('',
    url(r'^upload/$', 'user_photos.views.upload', name='user_photos-upload'),
    url(r'^photo/(?P<pk>\d+)/$',
        DetailView.as_view(model=Photo),
        name='user_photos-detail'),
    url(r'^gallery/(?P<username>[\w.@+-]{1,30})/$',
        GalleryView.as_view(),
        name='user_photos-gallery'),
    url(r'^delete/$', 'user_photos.views.delete', name='user_photos-delete'),
)
