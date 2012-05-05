"""urls for the contact application"""
from django.conf.urls import patterns, url

urlpatterns = patterns('contact.views',
   url(r'^$', 'contact_form', name='contact-form'),
   (r'^thanks/$', 'contact_thanks'),
)
