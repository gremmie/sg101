"""
Views for the oembed application.

"""
import json
import re

from django.http import HttpResponse
from django.http import HttpResponseBadRequest
from django.http import HttpResponseForbidden
from django.conf import settings

from oembed.models import Provider
from oembed.models import Oembed
from oembed.core import get_oembed


def fetch_media(request):
    """
    This view returns the HTML media of an embeddable resource as
    JSON. This view is the target of an AJAX request.
    """
    if not request.user.is_authenticated:
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
                data = get_oembed(provider.api_endpoint,
                                  url,
                                  maxwidth=settings.OEMBED_MAXWIDTH,
                                  maxheight=settings.OEMBED_MAXHEIGHT,
                                  scheme='https')
            except IOError as e:
                return HttpResponseBadRequest(
                    "Sorry, we could not retrieve your video (%s)" % e)

            data_type = data.get('type', '?')
            if data_type not in Oembed.ALLOWED_TYPES:
                return HttpResponseBadRequest(
                    "Hey, this doesn't look like a media type we support..??")

            oembed = Oembed(url=url,
                            type=Oembed.MEDIA_TYPE_REVERSE[data_type],
                            title=data.get('title', ''),
                            width=int(data.get('width', 0)),
                            height=int(data.get('height', 0)),
                            html=data.get('html', ''))
            oembed.save()

            data = dict(id=oembed.id, embed=oembed.html)
            return HttpResponse(json.dumps(data),
                    content_type='application/json')

    return HttpResponseBadRequest("Sorry, we couldn't find that video.")


def fetch_saved_media(request):
    """
    This view returns the HTML embed information for previously saved Oembed
    objects as JSON. This view is the target of an AJAX request.
    """
    if not request.user.is_authenticated:
        return HttpResponseForbidden('Please login or register.')

    embed_ids = request.GET.getlist('embeds')
    if not embed_ids:
        return HttpResponseBadRequest('Missing embed list.')

    embeds = Oembed.objects.in_bulk(embed_ids)

    # build results in order
    results = []
    for pk in embeds:
        results.append(dict(id=pk, html=embeds[pk].html))

    return HttpResponse(json.dumps(results), content_type='application/json')
