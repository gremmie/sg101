"""urls for the contact application"""
from django.conf.urls import patterns, url
from django.views.generic import TemplateView

urlpatterns = patterns('',
   url(r'^$', 'contact.views.contact_form', name='contact-form'),
   url(r'^thanks/$',
       TemplateView.as_view(template_name='contact/contact_thanks.html'),
       name='contact-thanks'),
)
