"""
URLs for the downloads application.
"""
from django.urls import path, re_path

import downloads.views

urlpatterns = [
    path('', downloads.views.index, name='downloads-index'),
    path('add/', downloads.views.add, name='downloads-add'),
    # Regex kept: 'sort' is a fixed choice set, not a stock converter shape.
    re_path(r'^category/(?P<slug>[\w\d-]+)/(?P<sort>title|date|rating|hits)/$',
       downloads.views.category,
       name='downloads-category'),
    path('details/<int:id>/', downloads.views.details, name='downloads-details'),
    path('new/', downloads.views.new, name='downloads-new'),
    path('popular/', downloads.views.popular, name='downloads-popular'),
    path('request/', downloads.views.request_download, name='downloads-request_download'),
    path('rate/', downloads.views.rate_download, name='downloads-rate'),
    path('rating/', downloads.views.rating, name='downloads-rating'),
    path('thanks/', downloads.views.thanks, name='downloads-add_thanks'),
]
