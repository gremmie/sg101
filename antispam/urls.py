"""URLs for the antispam application."""
from django.conf.urls import patterns, url

urlpatterns = patterns('antispam.views',
    url(r'^suspended/$', 'suspended', name='antispam-suspended'),
)
