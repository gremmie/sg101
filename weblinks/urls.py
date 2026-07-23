"""urls for the weblinks application"""
from django.urls import path, re_path

import weblinks.views as wv


urlpatterns = [
   path('', wv.link_index, name='weblinks-main'),
   path('add/', wv.add_link, name='weblinks-add_link'),
   path('add/thanks/', wv.add_thanks, name='weblinks-add_thanks'),
   # Regex kept: 'sort' is a fixed choice set, not a stock converter shape.
   re_path(r'^category/(?P<slug>[\w\d-]+)/(?P<sort>title|date|rating|hits)/$',
      wv.view_links,
      name='weblinks-view_links'),
   path('detail/<int:id>/',
      wv.link_detail,
      name='weblinks-link_detail'),
   path('new/', wv.new_links, name='weblinks-new_links'),
   path('popular/', wv.popular_links, name='weblinks-popular_links'),
   path('random/', wv.random_link, name='weblinks-random_link'),
   path('report/<int:link_id>/', wv.report_link, name='weblinks-report_link'),
   path('visit/<int:link_id>/', wv.visit, name="weblinks-visit"),
]
