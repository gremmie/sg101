"""
Url patterns for the contests application.

"""
from django.conf.urls.defaults import patterns, url
from django.views.generic import DetailView, ListView

from contests.models import Contest


urlpatterns = patterns('',
   url(r'^$',
       ListView.as_view(
           context_object_name='contests',
           queryset=Contest.public_objects.all()),
       name='contests-index'),

   url(r'^enter/$',
       'contests.views.enter',
       name='contests-enter'),

   url(r'^c/(?P<slug>[\w-]+)/$',
       DetailView.as_view(
           context_object_name='contest',
           queryset=Contest.public_objects.all().select_related('winner')),
       name='contests-contest'),
)
