"""
urls.py - URLs for the ygroup application.

"""
from django.conf.urls import url
from django.views.generic import DetailView

from ygroup.models import Post
from ygroup.views import ThreadIndexView, ThreadView


urlpatterns = [
    url(r'^threads/$',
        ThreadIndexView.as_view(),
        name='ygroup-thread_index'),
    url(r'^thread/(\d+)/$',
        ThreadView.as_view(),
        name='ygroup-thread_view'),
    url(r'^post/(?P<pk>\d+)/$',
        DetailView.as_view(model=Post, context_object_name='post'),
        name='ygroup-post_view'),
]
