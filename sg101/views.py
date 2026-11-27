"""Misc views for SG101"""

from django.views.generic import TemplateView


class HomePageView(TemplateView):
    template_name = 'home.html'


class StoreView(TemplateView):
    template_name = 'store/base.html'
