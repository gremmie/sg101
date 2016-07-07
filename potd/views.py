"""
Views for the POTD application.
"""

from django.shortcuts import render
from django.shortcuts import get_object_or_404

from potd.models import Current
from potd.models import Photo


def view(request):
    potd = Current.objects.get_current_photo()
    return render(request, 'potd/view.html', {
        'potd': potd,
        'is_current': True,
        'V3_DESIGN': True,
        })


def archive(request, id):
    photo = get_object_or_404(Photo, pk=id)
    return render(request, 'potd/view.html', {
        'potd': photo,
        'is_current': False,
        'V3_DESIGN': True,
        })
