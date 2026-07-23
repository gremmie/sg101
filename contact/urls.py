"""urls for the contact application"""
from django.urls import path

import contact.views

urlpatterns = [
   path('', contact.views.contact_form, name='contact-form'),
   path('thanks/',
       contact.views.ContactThanksView.as_view(),
       name='contact-thanks'),
]
