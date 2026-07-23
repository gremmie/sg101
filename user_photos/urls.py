"""URLs for the user_photos application."""
from django.urls import path, re_path

import user_photos.views


urlpatterns = [
    path('upload/', user_photos.views.upload, name='user_photos-upload'),
    path('upload-ajax/',
        user_photos.views.upload_ajax,
        name='user_photos-upload_ajax'),
    path('upload-ajax-v3/',
        user_photos.views.upload_ajax_v3,
        name='user_photos-upload_ajax_v3'),
    path('photo/<int:pk>/',
        user_photos.views.PhotoView.as_view(),
        name='user_photos-detail'),
    # Regex kept: username is length-bounded and allows '.@+-'.
    re_path(r'^gallery/(?P<username>[\w.@+-]{1,30})/$',
        user_photos.views.GalleryView.as_view(),
        name='user_photos-gallery'),
    path('delete/', user_photos.views.delete, name='user_photos-delete'),
    path('hotlink/',
        user_photos.views.hotlink_image,
        name='user_photos-hotlink'),
]
