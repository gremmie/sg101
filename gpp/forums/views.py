"""
Views for the forums application.
"""
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404
from django.shortcuts import render_to_response
from django.template import RequestContext

from forums.models import Forum
from forums.models import Topic
from forums.forms import NewTopicForm


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


@login_required
def new_topic(request, slug):
    """
    This view handles the creation of new topics.
    """
    forum = get_object_or_404(Forum, slug=slug)
    if request.method == 'POST':
        form = NewTopicForm(request.POST)
        if form.is_valid():
            topic = form.save(forum, request.user, request.META.get("REMOTE_ADDR"))
            return HttpResponseRedirect(reverse('forums-new_topic_thanks',
                                            kwargs={'tid': topic.pk}))
    else:
        form = NewTopicForm()
    
    return render_to_response('forums/new_topic.html', {
        'forum': forum,
        'form': form,
        },
        context_instance=RequestContext(request))


@login_required
def new_topic_thanks(request, tid):
    """
    This view displays the success page for a newly created topic.
    """
    topic = get_object_or_404(Topic, pk=tid)
    return render_to_response('forums/new_topic_thanks.html', {
        'forum': topic.forum,
        'topic': topic,
        },
        context_instance=RequestContext(request))
