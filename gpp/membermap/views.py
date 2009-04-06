"""
Views for the membermap application.
"""
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponse
from django.http import HttpResponseBadRequest
from django.http import HttpResponseForbidden
from django.views.decorators.http import require_POST

from membermap.models import MapEntry
from membermap.forms import MapEntryForm


def index(request):
    entry = None
    if request.user.is_authenticated():
        try:
            entry = MapEntry.objects.get(user=request.user)
        except MapEntry.DoesNotExist:
            pass
    if entry is not None:
        form = MapEntryForm(initial={
            'location': entry.location,
            'message': entry.message})
    else:
        form = MapEntryForm()

    return render_to_response('membermap/index.html', {
        'form': form,
        },
        context_instance = RequestContext(request))


def query(request):
    """
    This view is called by AJAX. If the user is logged in, return
    a JSON object that consists of:
        "users" : array of user objects
        "recent" : array of usernames recently modified
    """
    if request.user.is_authenticated():
        qs = MapEntry.objects.values_list('json', flat=True).order_by('user__username')
        s = '{"users":[' + ','.join(qs) + '], "recent":['

        names = MapEntry.objects.values_list('user__username', flat=True)[:10]
        s += ','.join(['"%s"' % name for name in names])
        s += ']}'
        return HttpResponse(s, content_type='application/json')

    return HttpResponseForbidden('You must be logged in.')


@require_POST
def add(request):
    """
    This view is called by AJAX to add/update the user to the map.
    It returns the new JSON representation of the user.
    """
    if not request.user.is_authenticated():
        return HttpResponseForbidden('You must be logged in.')

    loc = request.POST.get('loc', None)
    lat = request.POST.get('lat', None)
    lon = request.POST.get('lon', None)
    msg = request.POST.get('msg', '')

    if loc is None or lat is None or lon is None:
        return HttpResponseBadRequest('Missing parameters')

    try:
        lat = float(lat)
        lon = float(lon)
    except ValueError:
        return HttpResponseBadRequest('Invalid lat/lon')

    try:
        entry = MapEntry.objects.get(user=request.user)
    except MapEntry.DoesNotExist:
        entry = MapEntry(user=request.user)

    entry.location = loc
    entry.lat = lat
    entry.lon = lon
    entry.message = msg
    entry.save()

    return HttpResponse(entry.json, content_type='application/json')


@require_POST
def delete(request):
    """
    This view is called by AJAX to delete the user from the map.
    """
    if not request.user.is_authenticated():
        return HttpResponseForbidden('You must be logged in.')

    try:
        entry = MapEntry.objects.get(user=request.user)
    except MapEntry.DoesNotExist:
        pass
    else:
        entry.delete()

    return HttpResponse('')

# vim: ts=4 sw=4
