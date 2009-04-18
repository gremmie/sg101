"""
Views for the POTD application.
"""

from django.shortcuts import render_to_response
from django.shortcuts import get_object_or_404
from django.template import RequestContext

from potd.models import Current
from potd.models import Photo


def view(request):
    potd = Current.objects.get_current_photo()
    return render_to_response('potd/view.html', {
        'potd': potd,
        'is_current': True,
        },
        context_instance = RequestContext(request))

def archive(request, id):
    photo = get_object_or_404(Photo, pk=id)
    return render_to_response('potd/view.html', {
        'potd': photo,
        'is_current': False,
        },
        context_instance = RequestContext(request))
