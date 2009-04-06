"""urls for the News application"""
from django.conf.urls.defaults import *

urlpatterns = patterns('news.views',
   url(r'^page/(?P<page>\d+)/$', 'index', name='news-index_page'),
   url(r'^archive/$', 'archive_index', name='news-archive_index'),
   url(r'^archive/(?P<year>\d{4})/(?P<month>\d\d?)/page/(?P<page>\d+)/$', 
      'archive', 
      name='news-archive_page'),
   (r'^categories/$', 'category_index'),
   (r'^category/(?P<category>\d+)/page/(?P<page>\d+)/$', 'category'),
   (r'^email/(\d+)/$', 'email_story'),
   (r'^email/thanks/$', 'email_thanks'),
   url(r'^search/page/(?P<page>\d+)/$', 'search', name='news-search_page'),
   (r'^story/(\d+)/$', 'story'),
   (r'^submit/$', 'submit'),
   (r'^submit/thanks/$', 'submit_thanks'),
   url(r'^tags/$', 'tags', name='news-tag_index'),
   url(r'^tag/(?P<tag_name>[^/]+)/page/(?P<page>\d+)/$', 
      'tag', 
      name='news-tag_page'),
)

urlpatterns += patterns('django.views.generic.simple',
   (r'^$', 'redirect_to', {'url': 'page/1/'}),
)
