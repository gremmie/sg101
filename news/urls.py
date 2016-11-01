"""urls for the News application"""
from django.conf.urls import url

import news.views


urlpatterns = [
    url(r'^date/$', news.views.index, name='news-index_page'),
    url(r'^archive/$', news.views.archive_index, name='news-archive_index'),
    url(r'^archive/(?P<year>\d{4})/(?P<month>\d\d?)/$',
        news.views.archive,
        name='news-archive_page'),
    url(r'^categories/$', news.views.category_index, name='news-category_index'),
    url(r'^category/(?P<slug>[\w\d-]+)/$', news.views.category, name='news-category'),
    url(r'^email/(\d+)/$', news.views.email_story, name='news-email_story'),
    url(r'^email/(\d+)/thanks/$', news.views.email_thanks, name='news-email_thanks'),
    url(r'^story/(\d+)/$', news.views.story, name='news-story'),
    url(r'^submit/$', news.views.submit, name='news-submit'),
    url(r'^submit/thanks/$', news.views.submit_thanks, name='news-submit_thanks'),
    url(r'^tags/$', news.views.tags, name='news-tag_index'),
    url(r'^tag/(?P<tag_name>[^/]+)/$', news.views.tag, name='news-tag_page'),
]
