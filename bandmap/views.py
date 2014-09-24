"""Views for the bandmap application.

"""
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.contrib import messages as django_messages

from bandmap.forms import BandForm


SUCCESS = "Successfully submitted {} for admin review. Thanks!"


def map_view(request):
    return render(request, 'bandmap/map.html')


@login_required
def add_band(request):
    """
    Provides the ability for a user to submit a new band to the map.

    """
    if request.method == 'POST':
        form = BandForm(request.POST)
        if form.is_valid():
            band = form.save(commit=False)
            band.user = request.user
            band.save()
            django_messages.success(request, SUCCESS.format(band.name))
            redirect('bandmap-add')
    else:
        form = BandForm()

    return render(request, 'bandmap/add.html', {
        'form': form,
        })
