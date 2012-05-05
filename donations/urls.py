"""
URLs for the donations application.
"""
from django.conf.urls import patterns, url
from django.views.generic import TemplateView

urlpatterns = patterns('donations.views',
    url(r'^$', 'index', name='donations-index'),
    url(r'^ipn/$', 'ipn', name='donations-ipn'),
)
urlpatterns += patterns('',
    url(r'^thanks/$', TemplateView.as_view(template_name='donations/thanks.html'),
        name='donations-thanks'),
)
