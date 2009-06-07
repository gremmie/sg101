"""
URLs for the donations application.
"""
from django.conf.urls.defaults import *

urlpatterns = patterns('donations.views',
    url(r'^$', 'index', name='donations-index'),
    url(r'^ipn/$', 'ipn', name='donations-ipn'),
    url(r'^thanks/$', 'thanks', name='donations-thanks'),
)
