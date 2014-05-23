"""
Views for the membermap application.

"""
import json

from django.shortcuts import render_to_response
from django.template.loader import render_to_string
from django.template import RequestContext
from django.http import HttpResponse
from django.http import HttpResponseBadRequest
from django.http import HttpResponseForbidden
from django.views.decorators.http import require_POST
from django.core.cache import cache

from membermap.models import MapEntry
from membermap.forms import MapEntryForm
from bio.models import UserProfile

CACHE_KEY = 'membermap_json'
CACHE_TIMEOUT = 5 * 60


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
    if not request.user.is_authenticated():
        return HttpResponseForbidden('You must be logged in.')

    # Do we have all the JSON cached?
    s = cache.get(CACHE_KEY)
    if s:
        return HttpResponse(s, content_type='application/json')

    # Compute JSON for the map
    entries = MapEntry.objects.all().select_related().order_by('user__username')
    users = []
    user_ids = []
    recent = []
    for entry in entries.iterator():
        users.append(dict(name=entry.user.username,
            lat=entry.lat,
            lon=entry.lon,
            message=entry.html,
            ))
        user_ids.append(entry.user.id)
        recent.append((entry.date_updated, entry.user.username))

    # Get avatars for all users
    profiles = UserProfile.objects.filter(user__in=user_ids).select_related()
    avatars = {}
    for profile in profiles.iterator():
        if profile.avatar and profile.avatar.url:
            avatars[profile.user.username] = profile.avatar.url

    # Render the messages that go in the balloons
    for user in users:
        user['message'] = render_to_string('membermap/balloon.html',
                dict(user=user, avatar_url=avatars.get(user['name'])))

    # Produce the list of recent updates
    recent.sort(reverse=True)
    del recent[10:]
    recent = [entry[1] for entry in recent]

    # Create the JSON for the map
    result = dict(users=users, recent=recent)
    s = json.dumps(result, ensure_ascii=False)

    cache.set(CACHE_KEY, s, CACHE_TIMEOUT)
    return HttpResponse(s, content_type='application/json')


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

    cache.delete(CACHE_KEY)

    avatar_url = None
    profile = entry.user.profile
    if profile.avatar and profile.avatar.url:
        avatar_url = profile.avatar.url

    u = dict(name=entry.user.username,
            lat=entry.lat,
            lon=entry.lon,
            message=entry.html)

    u['message'] = render_to_string('membermap/balloon.html',
        dict(user=u, avatar_url=avatar_url))

    result = json.dumps(u, ensure_ascii=False)
    return HttpResponse(result, content_type='application/json')


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
        cache.delete(CACHE_KEY)

    return HttpResponse('')
