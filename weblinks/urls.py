"""urls for the weblinks application"""
from django.conf.urls import url

import weblinks.views as wv


urlpatterns = [
   url(r'^$', wv.link_index, name='weblinks-main'),
   url(r'^add/$', wv.add_link, name='weblinks-add_link'),
   url(r'^add/thanks/$', wv.add_thanks, name='weblinks-add_thanks'),
   url(r'^category/(?P<slug>[\w\d-]+)/(?P<sort>title|date|rating|hits)/$',
      wv.view_links,
      name='weblinks-view_links'),
   url(r'^detail/(\d+)/$',
      wv.link_detail,
      name='weblinks-link_detail'),
   url(r'^new/$', wv.new_links, name='weblinks-new_links'),
   url(r'^popular/$', wv.popular_links, name='weblinks-popular_links'),
   url(r'^random/$', wv.random_link, name='weblinks-random_link'),
   url(r'^report/(\d+)/$', wv.report_link, name='weblinks-report_link'),
   url(r'^visit/(\d+)/$', wv.visit, name="weblinks-visit"),
]
