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
from django.utils.text import wrap

from core.paginator import DiggPaginator
from core.functions import email_admins
from forums.models import Forum
from forums.models import Topic
from forums.models import Post
from forums.models import FlaggedPost
from forums.forms import NewTopicForm, NewPostForm, PostForm, MoveTopicForm

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

    topics = forum.topics.select_related('user', 'last_post', 'last_post__user')
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

    can_moderate = _can_moderate(topic.forum, request.user)

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
            _bump_post_count(request.user)
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
        return HttpResponseForbidden('Please login or register to post.')

    form = NewPostForm(request.POST)
    if form.is_valid():
        if not _can_post_in_topic(form.topic, request.user):
            return HttpResponseForbidden("You don't have permission to post in this topic.")

        post = form.save(request.user, request.META.get("REMOTE_ADDR", ""))
        _bump_post_count(request.user)
        return render_to_response('forums/display_post.html', {
            'post': post,
            },
            context_instance=RequestContext(request))

    return HttpResponseBadRequest("Invalid post.");


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

    can_moderate = _can_moderate(post.topic.forum, request.user)
    can_edit = can_moderate or request.user == post.user

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
        'can_moderate': can_moderate,
        },
        context_instance=RequestContext(request))


@require_POST
def delete_post(request):
    """
    This view function allows superusers and forum moderators to delete posts.
    This function is the target of AJAX calls from the client.
    """
    if not request.user.is_authenticated():
        return HttpResponseForbidden('Please login to delete a post.')

    id = request.POST.get('id')
    if id is None:
        return HttpResponseBadRequest('No post id')

    post = get_object_or_404(Post.objects.select_related(), pk=id)

    can_delete = request.user.is_superuser or \
            request.user in post.topic.forum.moderators.all()

    if not can_delete:
        return HttpResponseForbidden("You don't have permission to delete that post.")

    if post.topic.post_count == 1 and post == post.topic.last_post:
        _delete_topic(post.topic)
    else:
        _delete_post(post)

    return HttpResponse("The post has been deleted.")


def _delete_post(post):
    """
    Internal function to delete a single post object.
    Decrements the post author's post count.
    Adjusts the parent topic and forum's last_post as needed.
    """
    # Adjust post creator's post count
    profile = post.user.get_profile()
    if profile.forum_post_count > 0:
        profile.forum_post_count -= 1
        profile.save()

    # If this post is the last_post in a topic, we need to update
    # both the topic and parent forum's last post fields. If we don't
    # the cascading delete will delete them also!

    topic = post.topic
    if topic.last_post == post:
        topic.last_post_pre_delete()
        topic.save()

    forum = topic.forum
    if forum.last_post == post:
        forum.last_post_pre_delete()
        forum.save()

    # Should be safe to delete the post now:
    post.delete()


def _delete_topic(topic):
    """
    Internal function to delete an entire topic.
    Deletes the topic and all posts contained within.
    Adjusts the parent forum's last_post as needed.
    Note that we don't bother adjusting all the users'
    post counts as that doesn't seem to be worth the effort.
    """
    if topic.forum.last_post.topic == topic:
        topic.forum.last_post_pre_delete()
        topic.forum.save()

    # It should be safe to just delete the topic now. This will
    # automatically delete all posts in the topic.
    topic.delete()


@login_required
def new_post(request, topic_id):
    """
    This function is the view for creating a normal, non-quick reply
    to a topic.
    """
    topic = get_object_or_404(Topic.objects.select_related(), pk=topic_id)
    can_post = _can_post_in_topic(topic, request.user)

    if can_post:
        if request.method == 'POST':
            form = PostForm(request.POST)
            if form.is_valid():
                post = form.save(commit=False)
                post.topic = topic
                post.user = request.user
                post.user_ip = request.META.get("REMOTE_ADDR", "")
                post.save()
                _bump_post_count(request.user)
                return HttpResponseRedirect(post.get_absolute_url())
        else:
            quote_id = request.GET.get('quote')
            if quote_id:
                quote_post = get_object_or_404(Post.objects.select_related(),
                        pk=quote_id)
                form = PostForm(initial={'body': _quote_message(quote_post.user.username,
                    quote_post.body)})
            else:
                form = PostForm()
    else:
        form = None

    return render_to_response('forums/new_post.html', {
        'forum': topic.forum,
        'topic': topic,
        'form': form,
        'can_post': can_post,
        },
        context_instance=RequestContext(request))


@login_required
def mod_topic_stick(request, id):
    """
    This view function is for moderators to toggle the sticky status of a topic.
    """
    topic = get_object_or_404(Topic.objects.select_related(), pk=id)
    if _can_moderate(topic.forum, request.user):
        topic.sticky = not topic.sticky
        topic.save()
        return HttpResponseRedirect(topic.get_absolute_url())

    return HttpResponseForbidden()


@login_required
def mod_topic_lock(request, id):
    """
    This view function is for moderators to toggle the locked status of a topic.
    """
    topic = get_object_or_404(Topic.objects.select_related(), pk=id)
    if _can_moderate(topic.forum, request.user):
        topic.locked = not topic.locked
        topic.save()
        return HttpResponseRedirect(topic.get_absolute_url())

    return HttpResponseForbidden()


@login_required
def mod_topic_delete(request, id):
    """
    This view function is for moderators to delete an entire topic.
    """
    topic = get_object_or_404(Topic.objects.select_related(), pk=id)
    if _can_moderate(topic.forum, request.user):
        forum_url = topic.forum.get_absolute_url()
        _delete_topic(topic)
        return HttpResponseRedirect(forum_url)

    return HttpResponseForbidden()


@login_required
def mod_topic_move(request, id):
    """
    This view function is for moderators to move a topic to a different forum.
    """
    topic = get_object_or_404(Topic.objects.select_related(), pk=id)
    if not _can_moderate(topic.forum, request.user):
        return HttpResponseForbidden()

    if request.method == 'POST':
        form = MoveTopicForm(request.user, request.POST)
        if form.is_valid():
            new_forum = form.cleaned_data['forums']
            old_forum = topic.forum
            if new_forum != old_forum:
                topic.forum = new_forum
                topic.save()
                # Have to adjust foreign keys to last_post, denormalized counts, etc.:
                old_forum.topic_count_update()
                old_forum.post_count_update()
                old_forum.save()
                new_forum.topic_count_update()
                new_forum.post_count_update()
                new_forum.save()

            return HttpResponseRedirect(topic.get_absolute_url())
    else:
        form = MoveTopicForm(request.user)

    return render_to_response('forums/move_topic.html', {
        'forum': topic.forum,
        'topic': topic,
        'form': form,
        },
        context_instance=RequestContext(request))


def _can_moderate(forum, user):
    """
    Determines if a user has permission to moderate a given forum.
    """
    return user.is_authenticated() and (
            user.is_superuser or user in forum.moderators.all())


def _can_post_in_topic(topic, user):
    """
    This function returns true if the given user can post in the given topic
    and false otherwise.
    """
    return (not topic.locked and topic.forum.category.can_access(user)) or \
            (user.is_superuser or user in topic.forum.moderators.all())


def _bump_post_count(user):
    """
    Increments the forum_post_count for the given user.
    """
    profile = user.get_profile()
    profile.forum_post_count += 1
    profile.save()


def _quote_message(who, message):
   """
   Builds a message reply by quoting the existing message in a
   typical email-like fashion. The quoting is compatible with Markdown.
   """
   header = '*%s wrote:*\n\n' % (who, )
   lines = wrap(message, 55).split('\n')
   for i, line in enumerate(lines):
      lines[i] = '> ' + line
   return header + '\n'.join(lines)
