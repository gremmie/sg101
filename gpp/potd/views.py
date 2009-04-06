"""
Views for the POTD application.
"""

from django.shortcuts import render_to_response
from django.template import RequestContext

from potd.models import Current


def view(request):
    potd = Current.objects.get_current_photo()
    return render_to_response('potd/view.html', {
        'potd': potd,
        },
        context_instance = RequestContext(request))
