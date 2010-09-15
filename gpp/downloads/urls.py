"""
URLs for the downloads application.
"""
from django.conf.urls.defaults import *

urlpatterns = patterns('downloads.views',
    url(r'^$', 'index', name='downloads-index'),
    url(r'^add/$', 'add', name='downloads-add'),
    url(r'^category/(?P<slug>[\w\d-]+)/(?P<sort>title|date|rating|hits)/$',
       'category',
       name='downloads-category'),
    url(r'^details/(\d+)/$', 'details', name='downloads-details'),
    url(r'^(\d+)/$', 'download', name='downloads-download'),
    url(r'^new/$', 'new', name='downloads-new'),
    url(r'^popular/$', 'popular', name='downloads-popular'),
    url(r'^random/$', 'random_download', name='downloads-random'),
    url(r'^rate/$', 'rate_download', name='downloads-rate'),
    url(r'^rating/$', 'rating', name='downloads-rating'),
    url(r'^thanks/$', 'thanks', name='downloads-add_thanks'),
)
