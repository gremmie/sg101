"""URLs for the user_photos application."""
from django.conf.urls import url

import user_photos.views


urlpatterns = [
    url(r'^upload/$', user_photos.views.upload, name='user_photos-upload'),
    url(r'^upload-ajax/$',
        user_photos.views.upload_ajax,
        name='user_photos-upload_ajax'),
    url(r'^upload-ajax-v3/$',
        user_photos.views.upload_ajax_v3,
        name='user_photos-upload_ajax_v3'),
    url(r'^photo/(?P<pk>\d+)/$',
        user_photos.views.PhotoView.as_view(),
        name='user_photos-detail'),
    url(r'^gallery/(?P<username>[\w.@+-]{1,30})/$',
        user_photos.views.GalleryView.as_view(),
        name='user_photos-gallery'),
    url(r'^delete/$', user_photos.views.delete, name='user_photos-delete'),
    url(r'^hotlink/$',
        user_photos.views.hotlink_image,
        name='user_photos-hotlink'),
]
