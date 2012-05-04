"""urls for the weblinks application"""
from django.conf.urls import patterns, url

urlpatterns = patterns('weblinks.views',
   url(r'^$', 'link_index', name='weblinks-main'),
   url(r'^add/$', 'add_link', name='weblinks-add_link'),
   url(r'^add/thanks/$', 'add_thanks', name='weblinks-add_thanks'),
   url(r'^category/(?P<slug>[\w\d-]+)/(?P<sort>title|date|rating|hits)/$', 
      'view_links',
      name='weblinks-view_links'),
   url(r'^detail/(\d+)/$', 
      'link_detail',
      name='weblinks-link_detail'),
   url(r'^new/$', 'new_links', name='weblinks-new_links'),
   url(r'^popular/$', 'popular_links', name='weblinks-popular_links'),
   url(r'^random/$', 'random_link', name='weblinks-random_link'),
   url(r'^report/(\d+)/$', 'report_link', name='weblinks-report_link'),
   url(r'^visit/(\d+)/$', 'visit', name="weblinks-visit"),
)
