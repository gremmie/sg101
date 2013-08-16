"""
This module contains views for working with post attachments.

"""
import json

from django.http import HttpResponse
from django.http import HttpResponseForbidden
from django.http import HttpResponseBadRequest
from django.http import HttpResponseNotFound

from forums.models import Post


def fetch_attachments(request):
    """
    This view is the target of an AJAX GET request to retrieve the
    attachment embed data for a given forum post.

    """
    if not request.user.is_authenticated():
        return HttpResponseForbidden('Please login or register.')

    post_id = request.GET.get('pid')
    if post_id is None:
        return HttpResponseBadRequest('Missing post ID.')

    try:
        post = Post.objects.get(pk=post_id)
    except Post.DoesNotExist:
        return HttpResponseNotFound("That post doesn't exist.")

    embeds = post.attachments.all().select_related('embed')
    data = [{'id': embed.id, 'html': embed.html} for embed in embeds]

    return HttpResponse(json.dumps(data), content_type='application/json')

