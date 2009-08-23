"""
Views for the forums application.
"""
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.shortcuts import render_to_response
from django.template import RequestContext

from forums.models import Forum


def index(request):
    """
    This view displays all the forums available, ordered in each category.
    """
    forums = Forum.objects.all().select_related()
    cats = {}
    for forum in forums:
        cat = cats.setdefault(forum.category.id, {
            'cat': forum.category,
            'forums': [],
            })
        cat['forums'].append(forum)

    cmpdef = lambda a, b: cmp(a['cat'].position, b['cat'].position)
    cats = sorted(cats.values(), cmpdef)

    return render_to_response('forums/index.html', {
        'cats': cats,
        },
        context_instance=RequestContext(request))


def forum_index(request, slug):
    """
    Displays all the topics in a forum.
    """
    forum = get_object_or_404(Forum, slug=slug)
    topics = forum.topics.select_related()
    
    return render_to_response('forums/forum_index.html', {
        'forum': forum,
        'topics': topics,
        },
        context_instance=RequestContext(request))


def topic_index(request, id):
    """
    Displays all the posts in a topic.
    """
    raise Http404
