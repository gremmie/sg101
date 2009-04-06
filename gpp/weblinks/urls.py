"""urls for the weblinks application"""
from django.conf.urls.defaults import *

urlpatterns = patterns('weblinks.views',
   url(r'^$', 'link_index', name='weblinks-main'),
   (r'^add/$', 'add_link'),
   (r'^add/thanks/$', 'add_thanks'),
   url(r'^category/(?P<category>\d+)/(?P<sort>title|date|rating|hits)/page/(?P<page>\d+)/$', 
      'view_links',
      name='weblinks-view_links'),
   (r'^new/$', 'new_links'),
   (r'^popular/$', 'popular_links'),
   (r'^random/$', 'random_link'),
   (r'^report/(\d+)/$', 'report_link'),
   (r'^report/thanks/(\d+)$', 'report_thanks'),
   url(r'^search/page/(?P<page>\d+)/$', 
      'search_links',
      name="weblinks-search"),
   (r'^visit/(\d+)/$', 'visit'),
)
