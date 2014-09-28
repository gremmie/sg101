"""Views for the bandmap application.

"""
import json

from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.contrib import messages as django_messages
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.core.cache import cache

from bandmap.forms import BandForm
from bandmap.models import BandEntry


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
            return redirect('bandmap-add')
    else:
        form = BandForm()

    return render(request, 'bandmap/add.html', {
        'form': form,
        })


def query(request):
    """Retrieves the band map entries and returns them as JSON.

    """
    show_param = request.GET.get('show', 'all')
    if show_param not in ['all', 'active', 'inactive']:
        show_param = 'all'

    # Do we have the results cached already?
    cache_key = 'bandmap-results-{}'.format(show_param)
    results = cache.get(cache_key)
    if results:
        return HttpResponse(results, content_type='application/json')

    # Generate results
    qs = BandEntry.objects.filter(is_approved=True)
    if show_param == 'active':
        qs = qs.filter(is_active=True)
    elif show_param == 'inactive':
        qs = qs.filter(is_active=False)

    bands = []
    for band in qs.iterator():
        bands.append({
            'name': band.name,
            'url': band.url,
            'lat': band.lat,
            'lon': band.lon,
            'is_active': band.is_active,
            'note': render_to_string('bandmap/balloon.html', {'band': band}),
        })
    results = json.dumps(bands)

    # Store in cache
    cache.set(cache_key, results, 300)

    return HttpResponse(results, content_type='application/json')
