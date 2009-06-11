"""
URLs for the donations application.
"""
from django.conf.urls.defaults import *

urlpatterns = patterns('donations.views',
    url(r'^$', 'index', name='donations-index'),
    url(r'^ipn/$', 'ipn', name='donations-ipn'),
)
urlpatterns += patterns('django.views.generic.simple',
    (r'^thanks/$', 'direct_to_template', 
        {'template': 'donations/thanks.html'}, 'donations-thanks')
)
