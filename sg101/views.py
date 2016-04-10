"""Misc views for SG101"""

from django.views.generic import TemplateView


class StoreView(TemplateView):
    template_name = 'store/base.html'

    def get_context_data(self, **kwargs):
        context = super(StoreView, self).get_context_data(**kwargs)
        context['V3_DESIGN'] = True
        return context
