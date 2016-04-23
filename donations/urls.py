"""
URLs for the donations application.
"""
from django.conf.urls import url

import donations.views


urlpatterns = [
    url(r'^$', donations.views.index, name='donations-index'),
    url(r'^ipn/$', donations.views.ipn, name='donations-ipn'),
    url(r'^thanks/$', donations.views.ThanksView.as_view(), name='donations-thanks'),
]
