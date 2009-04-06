"""urls for the contact application"""
from django.conf.urls.defaults import *

urlpatterns = patterns('contact.views',
   url(r'^$', 'contact_form', name='contact-form'),
   (r'^thanks/$', 'contact_thanks'),
)
