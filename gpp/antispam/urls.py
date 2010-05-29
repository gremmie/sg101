"""URLs for the antispam application."""
from django.conf.urls.defaults import *

urlpatterns = patterns('antispam.views',
    url(r'^suspended/$', 'suspended', name='antispam-suspended'),
)
