"""
URLs for the downloads application.
"""
from django.conf.urls import url

import downloads.views

urlpatterns = [
    url(r'^$', downloads.views.index, name='downloads-index'),
    url(r'^add/$', downloads.views.add, name='downloads-add'),
    url(r'^category/(?P<slug>[\w\d-]+)/(?P<sort>title|date|rating|hits)/$',
       downloads.views.category,
       name='downloads-category'),
    url(r'^details/(\d+)/$', downloads.views.details, name='downloads-details'),
    url(r'^new/$', downloads.views.new, name='downloads-new'),
    url(r'^popular/$', downloads.views.popular, name='downloads-popular'),
    url(r'^request/$', downloads.views.request_download, name='downloads-request_download'),
    url(r'^rate/$', downloads.views.rate_download, name='downloads-rate'),
    url(r'^rating/$', downloads.views.rating, name='downloads-rating'),
    url(r'^thanks/$', downloads.views.thanks, name='downloads-add_thanks'),
]
