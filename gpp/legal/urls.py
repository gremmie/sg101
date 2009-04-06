"""urls for the legal application"""
from django.conf.urls.defaults import *

urlpatterns = patterns('legal.views',
   (r'^policy/(\w+)/$', 'view'),
)
