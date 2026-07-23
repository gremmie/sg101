"""
URLs for the donations application.
"""
from django.urls import path

import donations.views


urlpatterns = [
    path('', donations.views.index, name='donations-index'),
    path('ipn/', donations.views.ipn, name='donations-ipn'),
    path('thanks/', donations.views.ThanksView.as_view(), name='donations-thanks'),
]
