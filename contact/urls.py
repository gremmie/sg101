"""urls for the contact application"""
from django.conf.urls import url

import contact.views

urlpatterns = [
   url(r'^$', contact.views.contact_form, name='contact-form'),
   url(r'^thanks/$',
       contact.views.ContactThanksView.as_view(),
       name='contact-thanks'),
]
