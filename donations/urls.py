"""
URLs for the donations application.
"""
from django.conf.urls import url
from django.views.generic import TemplateView

import donations.views


urlpatterns = [
    url(r'^$', donations.views.index, name='donations-index'),
    url(r'^ipn/$', donations.views.ipn, name='donations-ipn'),
    url(r'^thanks/$', TemplateView.as_view(template_name='donations/thanks.html'),
        name='donations-thanks'),
]
