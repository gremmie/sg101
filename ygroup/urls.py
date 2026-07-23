"""
urls.py - URLs for the ygroup application.

"""
from django.urls import path, re_path

from ygroup.views import ThreadIndexView, ThreadView, PostView


urlpatterns = [
    path('threads/',
        ThreadIndexView.as_view(),
        name='ygroup-thread_index'),
    # Regex kept: ThreadView reads the id positionally (self.args[0]); path()
    # only produces keyword captures, which would leave self.args empty.
    re_path(r'^thread/(\d+)/$',
        ThreadView.as_view(),
        name='ygroup-thread_view'),
    path('post/<int:pk>/',
        PostView.as_view(),
        name='ygroup-post_view'),
]
