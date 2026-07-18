"""
Views for the podcast application.

"""
import json
import os.path
from six.moves.urllib.parse import urlparse

from django.shortcuts import render
from django.shortcuts import get_object_or_404

from podcast.models import Channel
from podcast.models import Item


def get_ext_from_url(url):
     """
     This function returns the extension part of the path from the given
     url.
     """
     ext = os.path.splitext(urlparse(url).path)[1]
     if ext.startswith('.'):
          ext = ext[1:]
     return ext


def jplayer_params(ext, url, alt_ext, alt_url):
     """
     Compute and returns a 2-tuple: (jplayer_media, jplayer_supplied)
     where
          jplayer_media: a string representation of the JSON for the
                jplayer setMedia parameter
          jplayer_supplied: the string for the jplayer supplied parameter

     media_list is an input list or tuple of 2-tuples of the form
          (media_type, url)
     where media_type is e.g. mp3, m4a, ogg, etc.

     """
     media = dict([(ext, url)])
     if alt_ext and alt_url:
          media[alt_ext] = alt_url

     # prefer mp4 to mp3
     if alt_ext is None:
          supplied = [ext]
     elif ext == "m4a":
          supplied = (ext, alt_ext)
     else:
          supplied = (alt_ext, ext)

     supplied = ", ".join(supplied)

     return json.dumps(media), supplied


def index(request):
    try:
        channel = Channel.objects.get(pk=1)
    except Channel.DoesNotExist:
        channel = None

    return render(request, 'podcast/index.html', {
        'channel': channel,
        'V3_DESIGN': True,
        })


def detail(request, id):
    podcast = get_object_or_404(Item.objects.select_related(), pk=id)

    ext = get_ext_from_url(podcast.enclosure_url)
    alt_ext = None
    if podcast.alt_enclosure_url:
        alt_ext = get_ext_from_url(podcast.alt_enclosure_url)

    jplayer_media, jplayer_supplied = jplayer_params(ext, podcast.enclosure_url,
              alt_ext, podcast.alt_enclosure_url)

    return render(request, 'podcast/detail.html', {
        'channel': podcast.channel,
        'podcast': podcast,
        'ext': ext,
        'alt_ext': alt_ext,
        'jplayer_media': jplayer_media,
        'jplayer_supplied': jplayer_supplied,
        'V3_DESIGN': True,
        })


def feed(request):
    try:
        channel = Channel.objects.get(pk=1)
    except Channel.DoesNotExist:
        channel = None

    if channel:
        channel.items = Item.objects.filter(channel=channel)

    return render(request, 'podcast/feed.xml', {
        'channel': channel,
        })
