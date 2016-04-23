"""
urls.py - URLs for the ygroup application.

"""
from django.conf.urls import url

from ygroup.views import ThreadIndexView, ThreadView, PostView


urlpatterns = [
    url(r'^threads/$',
        ThreadIndexView.as_view(),
        name='ygroup-thread_index'),
    url(r'^thread/(\d+)/$',
        ThreadView.as_view(),
        name='ygroup-thread_view'),
    url(r'^post/(?P<pk>\d+)/$',
        PostView.as_view(),
        name='ygroup-post_view'),
]
