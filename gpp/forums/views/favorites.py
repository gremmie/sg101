"""
This module contains view functions related to forum favorites (bookmarks).
"""
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponseRedirect
from django.http import HttpResponseForbidden
from django.http import Http404

from core.paginator import DiggPaginator
from forums.models import Topic


@login_required
@require_POST
def favorite_topic(request, topic_id):
    """
    This function handles the "favoriting" (bookmarking) of a forum topic by a
    user.
    """
    topic = get_object_or_404(Topic.objects.select_related(), id=topic_id)
    if topic.forum.category.can_access(request.user):
        topic.bookmarkers.add(request.user)
        return HttpResponseRedirect(
            reverse("forums-favorites_status", args=[topic.id]))
    raise Http404   # TODO return HttpResponseForbidden instead


@login_required
def manage_favorites(request):
    """Display a user's favorite topics and allow them to be deleted."""

    user = request.user
    if request.method == "POST":
        if request.POST.get('delete_all'):
            user.favorite_topics.clear()
        else:
            delete_ids = request.POST.getlist('delete_ids')
            try:
                delete_ids = [int(id) for id in delete_ids]
            except ValueError:
                raise Http404
            for topic in user.favorite_topics.filter(id__in=delete_ids):
                user.favorite_topics.remove(topic)

        page_num = request.POST.get('page', 1)
    else:
        page_num = request.GET.get('page', 1)

    topics = user.favorite_topics.select_related().order_by('-update_date')
    paginator = DiggPaginator(topics, 20, body=5, tail=2, margin=3, padding=2)
    try:
        page_num = int(page_num)
    except ValueError:
        page_num = 1
    try:
        page = paginator.page(page_num)
    except InvalidPage:
        raise Http404

    return render_to_response('forums/manage_topics.html', {
        'page_title': 'Favorite Topics',
        'description': 'Your favorite topics are listed below.',
        'page': page,
        },
        context_instance=RequestContext(request))

@login_required
def favorites_status(request, topic_id):
    """Display the favorite status for the given topic."""
    topic = get_object_or_404(Topic.objects.select_related(), id=topic_id)
    is_favorite = request.user in topic.bookmarkers.all()
    return render_to_response('forums/favorite_status.html', {
        'topic': topic,
        'is_favorite': is_favorite,
        },
        context_instance=RequestContext(request))

@login_required
@require_POST
def unfavorite_topic(request, topic_id):
    """
    Un-favorite the user from the requested topic.
    """
    topic = get_object_or_404(Topic, id=topic_id)
    topic.bookmarkers.remove(request.user)
    return HttpResponseRedirect(
        reverse("forums-favorites_status", args=[topic.id]))
