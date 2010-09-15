"""urls for the News application"""
from django.conf.urls.defaults import *

urlpatterns = patterns('news.views',
    url(r'^date/$', 'index', name='news-index_page'),
    url(r'^archive/$', 'archive_index', name='news-archive_index'),
    url(r'^archive/(?P<year>\d{4})/(?P<month>\d\d?)/$',
        'archive', 
        name='news-archive_page'),
    url(r'^categories/$', 'category_index', name='news-category_index'),
    url(r'^category/(?P<slug>[\w\d-]+)/$', 'category', name='news-category'),
    url(r'^email/(\d+)/$', 'email_story', name='news-email_story'),
    url(r'^email/thanks/$', 'email_thanks', name='news-email_thanks'),
    url(r'^story/(\d+)/$', 'story', name='news-story'),
    url(r'^submit/$', 'submit', name='news-submit'),
    url(r'^submit/thanks/$', 'submit_thanks', name='news-submit_thanks'),
    url(r'^tags/$', 'tags', name='news-tag_index'),
    url(r'^tag/(?P<tag_name>[^/]+)/$', 'tag', name='news-tag_page'),
)
