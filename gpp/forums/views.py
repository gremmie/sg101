"""
Views for the forums application.
"""
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.http import HttpResponse
from django.http import HttpResponseBadRequest
from django.http import HttpResponseForbidden
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.core.paginator import InvalidPage
from django.shortcuts import get_object_or_404
from django.shortcuts import render_to_response
from django.template.loader import render_to_string
from django.template import RequestContext
from django.views.decorators.http import require_POST

from core.paginator import DiggPaginator
from core.functions import email_admins
from forums.models import Forum
from forums.models import Topic
from forums.models import Post
from forums.models import FlaggedPost
from forums.forms import NewTopicForm, NewPostForm, PostForm

#######################################################################

TOPICS_PER_PAGE = 50
POSTS_PER_PAGE = 2

def create_topic_paginator(topics):
   return DiggPaginator(topics, TOPICS_PER_PAGE, body=5, tail=2, margin=3, padding=2)

def create_post_paginator(posts):
   return DiggPaginator(posts, POSTS_PER_PAGE, body=5, tail=2, margin=3, padding=2)

#######################################################################

def index(request):
    """
    This view displays all the forums available, ordered in each category.
    """
    forums = Forum.objects.forums_for_user(request.user)
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
    forum = get_object_or_404(Forum.objects.select_related(), slug=slug)

    if not forum.category.can_access(request.user):
        return HttpResponseForbidden()

    topics = forum.topics.select_related('last_post', 'last_post__user')
    paginator = create_topic_paginator(topics)
    page_num = int(request.GET.get('page', 1))
    try:
        page = paginator.page(page_num)
    except InvalidPage:
        raise Http404

    # we do this for the template since it is rendered twice
    page_nav = render_to_string('forums/pagination.html', {'page': page})
    
    return render_to_response('forums/forum_index.html', {
        'forum': forum,
        'page': page,
        'page_nav': page_nav,
        },
        context_instance=RequestContext(request))


def topic_index(request, id):
    """
    Displays all the posts in a topic.
    """
    topic = get_object_or_404(Topic.objects.select_related(), pk=id)

    if not topic.forum.category.can_access(request.user):
        return HttpResponseForbidden()

    topic.view_count += 1
    topic.save()

    posts = topic.posts.select_related()
    paginator = create_post_paginator(posts)
    page_num = int(request.GET.get('page', 1))
    try:
        page = paginator.page(page_num)
    except InvalidPage:
        raise Http404

    last_page = page_num == paginator.num_pages

    # we do this for the template since it is rendered twice
    page_nav = render_to_string('forums/pagination.html', {'page': page})

    can_moderate = request.user.is_authenticated() and (
        request.user.is_superuser or \
        request.user in topic.forum.moderators.all())

    can_reply = request.user.is_authenticated() and (
        not topic.locked or can_moderate)

    return render_to_response('forums/topic.html', {
        'forum': topic.forum,
        'topic': topic,
        'page': page,
        'page_nav': page_nav,
        'last_page': last_page,
        'can_moderate': can_moderate,
        'can_reply': can_reply,
        'form': NewPostForm(initial={'topic_id': topic.id}),
        },
        context_instance=RequestContext(request))


@login_required
def new_topic(request, slug):
    """
    This view handles the creation of new topics.
    """
    forum = get_object_or_404(Forum.objects.select_related(), slug=slug)

    if not forum.category.can_access(request.user):
        return HttpResponseForbidden()

    if request.method == 'POST':
        form = NewTopicForm(request.user, forum, request.POST)
        if form.is_valid():
            topic = form.save(request.META.get("REMOTE_ADDR"))
            return HttpResponseRedirect(reverse('forums-new_topic_thanks',
                                            kwargs={'tid': topic.pk}))
    else:
        form = NewTopicForm(request.user, forum)
    
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
    topic = get_object_or_404(Topic.objects.select_related(), pk=tid)
    return render_to_response('forums/new_topic_thanks.html', {
        'forum': topic.forum,
        'topic': topic,
        },
        context_instance=RequestContext(request))


@require_POST
def quick_reply_ajax(request):
    """
    This function handles the quick reply to a thread function. This
    function is meant to be the target of an AJAX post, and returns
    the HTML for the new post, which the client-side script appends
    to the document.
    """
    if not request.user.is_authenticated():
        return HttpResponseForbidden()

    form = NewPostForm(request.POST)
    if form.is_valid():
        if form.topic.locked or not form.topic.forum.category.can_access(request.user):
            return HttpResponseForbidden()

        post = form.save(request.user, request.META.get("REMOTE_ADDR"))
        return render_to_response('forums/display_post.html', {
            'post': post,
            },
            context_instance=RequestContext(request))

    return HttpResponseBadRequest();


def goto_post(request, post_id):
    """
    This function calculates what page a given post is on, then redirects
    to that URL. This function is the target of get_absolute_url() for
    Post objects.
    """
    post = get_object_or_404(Post.objects.select_related(), pk=post_id)
    count = post.topic.posts.filter(creation_date__lt=post.creation_date).count()
    page = count / POSTS_PER_PAGE + 1
    url = reverse('forums-topic_index', kwargs={'id': post.topic.id}) + \
        '?page=%s#p%s' % (page, post.id)
    return HttpResponseRedirect(url)


@require_POST
def flag_post(request):
    """
    This function handles the flagging of posts by users. This function should
    be the target of an AJAX post.
    """
    if not request.user.is_authenticated():
        return HttpResponseForbidden('Please login or register to flag a post.')

    id = request.POST.get('id')
    if id is None:
        return HttpResponseBadRequest('No post id')

    try:
        post = Post.objects.get(pk=id)
    except Post.DoesNotExist:
        return HttpResponseBadRequest('No post with id %s' % id)

    flag = FlaggedPost(user=request.user, post=post)
    flag.save()
    email_admins('A Post Has Been Flagged', """Hello,

A user has flagged a forum post for review.
""")
    return HttpResponse('The post was flagged. A moderator will review the post shortly. ' \
            'Thanks for helping to improve the discussions on this site.')


@login_required
def edit_post(request, id):
    """
    This view function allows authorized users to edit posts.
    The superuser, forum moderators, and original author can edit posts.
    """
    post = get_object_or_404(Post.objects.select_related(), pk=id)
    can_edit = request.user == post.user or \
            request.user.is_superuser or \
            request.user in post.topic.forum.moderators.all()

    if not can_edit:
        return HttpResponseForbidden("You don't have permission to edit that post.")

    if request.method == "POST":
        form = PostForm(request.POST, instance=post)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(post.get_absolute_url())
    else:
        form = PostForm(instance=post)

    return render_to_response('forums/edit_post.html', {
        'forum': post.topic.forum,
        'topic': post.topic,
        'post': post,
        'form': form,
        'can_moderate': True,
        },
        context_instance=RequestContext(request))
