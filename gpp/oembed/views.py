"""
Views for the oembed application.
"""
import re
import urllib2

from django.http import HttpResponse
from django.http import HttpResponseBadRequest
from django.http import HttpResponseForbidden
import django.utils.simplejson as json

from oembed.models import Provider
from oembed.models import Oembed
from oembed.core import get_oembed


def fetch_media(request):
    """
    This view returns the HTML media of an embeddable resource.
    This view is the target of an AJAX request. 
    """
    if not request.user.is_authenticated():
        return HttpResponseForbidden('Please login or register.')

    url = request.POST.get('q')

    if not url:
        return HttpResponseBadRequest('Please provide a valid URL.')

    # Is this already in our database?
    try:
        oembed = Oembed.objects.get(url=url)
    except Oembed.DoesNotExist:
        pass
    else:
        data = dict(id=oembed.id, embed=oembed.html)
        return HttpResponse(json.dumps(data), content_type='application/json')

    # It isn't in the database, try to find it from our providers
    providers = Provider.objects.all()
    for provider in providers:
        if re.match(provider.url_regex, url):
            try:
                data = get_oembed(provider.api_endpoint, url)
            except IOError, e:
                return HttpResponseBadRequest(
                    "Sorry, we could not retrieve your video (%s)" % e)

            if 'type' not in data or data['type'] != 'video':
                return HttpResponseBadRequest(
                    "Hey, this doesn't look like a video..??")

            oembed = Oembed(url=url,
                    type=Oembed.VIDEO,
                    title=data.get('title', ''),
                    width=int(data.get('width', 0)),
                    height=int(data.get('height', 0)),
                    html=data.get('html', ''))
            oembed.save()

            data = dict(id=oembed.id, embed=oembed.html)
            return HttpResponse(json.dumps(data),
                    content_type='application/json')

    return HttpBadRequest("Sorry, we couldn't find that video.")
