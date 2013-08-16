"""
Views for the forums application.

"""
import collections
import datetime

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
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
from django.db.models import F

import antispam
import antispam.utils
from bio.models import UserProfile, BadgeOwnership
from core.paginator import DiggPaginator
from core.functions import email_admins, quote_message

from forums.models import (Forum, Topic, Post, FlaggedPost, TopicLastVisit,
        ForumLastVisit, Attachment)
from forums.forms import (NewTopicForm, NewPostForm, PostForm, MoveTopicForm,
        SplitTopicForm)
from forums.unread import (get_forum_unread_status, get_topic_unread_status,
        get_post_unread_status, get_unread_topics)

import forums.permissions as perms
from forums.signals import (notify_new_topic, notify_updated_topic,
        notify_new_post, notify_updated_post)
from forums.latest import get_latest_topic_ids

#######################################################################

TOPICS_PER_PAGE = 50
POSTS_PER_PAGE = 20
FEED_BASE = '/feeds/forums/'
FORUM_FEED = FEED_BASE + '%s/'


def get_page_num(request):
    """Returns the value of the 'page' variable in GET if it exists, or 1
    if it does not."""

    try:
        page_num = int(request.GET.get('page', 1))
    except ValueError:
        page_num = 1

    return page_num


def create_topic_paginator(topics):
   return DiggPaginator(topics, TOPICS_PER_PAGE, body=5, tail=2, margin=3, padding=2)

def create_post_paginator(posts):
   return DiggPaginator(posts, POSTS_PER_PAGE, body=5, tail=2, margin=3, padding=2)


def attach_topic_page_ranges(topics):
    """Attaches a page_range attribute to each topic in the supplied list.
    This attribute will be None if it is a single page topic. This is used
    by the templates to generate "goto page x" links.
    """
    for topic in topics:
        if topic.post_count > POSTS_PER_PAGE:
            pp = DiggPaginator(range(topic.post_count), POSTS_PER_PAGE,
                    body=2, tail=3, margin=1)
            topic.page_range = pp.page(1).page_range
        else:
            topic.page_range = None

#######################################################################

def index(request):
    """
    This view displays all the forums available, ordered in each category.
    """
    public_forums = Forum.objects.public_forums()
    feeds = [{'name': 'All Forums', 'feed': FEED_BASE}]

    forums = Forum.objects.forums_for_user(request.user)
    get_forum_unread_status(forums, request.user)
    cats = {}
    for forum in forums:
        forum.has_feed = forum in public_forums
        if forum.has_feed:
            feeds.append({
                'name': '%s Forum' % forum.name,
                'feed': FORUM_FEED % forum.slug,
                })

        cat = cats.setdefault(forum.category.id, {
            'cat': forum.category,
            'forums': [],
            })
        cat['forums'].append(forum)

    cmpdef = lambda a, b: cmp(a['cat'].position, b['cat'].position)
    cats = sorted(cats.values(), cmpdef)

    return render_to_response('forums/index.html', {
        'cats': cats,
        'feeds': feeds,
        },
        context_instance=RequestContext(request))


def forum_index(request, slug):
    """
    Displays all the topics in a forum.
    """
    forum = get_object_or_404(Forum.objects.select_related(), slug=slug)

    if not perms.can_access(forum.category, request.user):
        return HttpResponseForbidden()

    feed = None
    if not forum.category.groups.all():
        feed = {
            'name': '%s Forum' % forum.name,
            'feed': FORUM_FEED % forum.slug,
        }

    topics = forum.topics.select_related('user', 'last_post', 'last_post__user')
    paginator = create_topic_paginator(topics)
    page_num = get_page_num(request)
    try:
        page = paginator.page(page_num)
    except InvalidPage:
        raise Http404

    get_topic_unread_status(forum, page.object_list, request.user)
    attach_topic_page_ranges(page.object_list)

    # we do this for the template since it is rendered twice
    page_nav = render_to_string('forums/pagination.html', {'page': page})

    can_moderate = perms.can_moderate(forum, request.user)

    return render_to_response('forums/forum_index.html', {
        'forum': forum,
        'feed': feed,
        'page': page,
        'page_nav': page_nav,
        'can_moderate': can_moderate,
        },
        context_instance=RequestContext(request))


def topic_index(request, id):
    """
    Displays all the posts in a topic.
    """
    topic = get_object_or_404(Topic.objects.select_related(
        'forum', 'forum__category', 'last_post'), pk=id)

    if not perms.can_access(topic.forum.category, request.user):
        return HttpResponseForbidden()

    topic.view_count = F('view_count') + 1
    topic.save(force_update=True)

    posts = topic.posts.select_related('user')

    paginator = create_post_paginator(posts)
    page_num = get_page_num(request)
    try:
        page = paginator.page(page_num)
    except InvalidPage:
        raise Http404
    get_post_unread_status(topic, page.object_list, request.user)

    # Attach user profiles to each post's user to avoid using
    # get_user_profile() in the template.
    users = set(post.user.id for post in page.object_list)

    profiles = UserProfile.objects.filter(user__id__in=users).select_related()
    profile_keys = [profile.id for profile in profiles]
    user_profiles = dict((profile.user.id, profile) for profile in profiles)

    last_post_on_page = None
    for post in page.object_list:
        post.user.user_profile = user_profiles[post.user.id]
        post.attach_list = []
        last_post_on_page = post

    # Attach badge ownership info to the user profiles to avoid lots
    # of database hits in the template:
    bos_qs = BadgeOwnership.objects.filter(
            profile__id__in=profile_keys).select_related()
    bos = collections.defaultdict(list)
    for bo in bos_qs:
        bos[bo.profile.id].append(bo)

    for user_id, profile in user_profiles.iteritems():
        profile.badge_ownership = bos[profile.id]

    # Attach any attachments
    post_ids = [post.pk for post in page.object_list]
    attachments = Attachment.objects.filter(post__in=post_ids).select_related(
            'embed').order_by('order')

    post_dict = dict((post.pk, post) for post in page.object_list)
    for item in attachments:
        post_dict[item.post.id].attach_list.append(item.embed)

    last_page = page_num == paginator.num_pages

    if request.user.is_authenticated():
        if last_page or last_post_on_page is None:
            visit_time = datetime.datetime.now()
        else:
            visit_time = last_post_on_page.creation_date
        _update_last_visit(request.user, topic, visit_time)

    # we do this for the template since it is rendered twice
    page_nav = render_to_string('forums/pagination.html', {'page': page})

    can_moderate = perms.can_moderate(topic.forum, request.user)

    can_reply = request.user.is_authenticated() and (
        not topic.locked or can_moderate)

    is_favorite = request.user.is_authenticated() and (
            topic in request.user.favorite_topics.all())

    is_subscribed = request.user.is_authenticated() and (
            topic in request.user.subscriptions.all())

    return render_to_response('forums/topic.html', {
        'forum': topic.forum,
        'topic': topic,
        'page': page,
        'page_nav': page_nav,
        'last_page': last_page,
        'can_moderate': can_moderate,
        'can_reply': can_reply,
        'form': NewPostForm(initial={'topic_id': topic.id}),
        'is_favorite': is_favorite,
        'is_subscribed': is_subscribed,
        },
        context_instance=RequestContext(request))


def topic_unread(request, id):
    """
    This view redirects to the first post the user hasn't read, if we can
    figure that out. Otherwise we redirect to the topic.

    """
    topic_url = reverse('forums-topic_index', kwargs={'id': id})

    if request.user.is_authenticated():
        topic = get_object_or_404(Topic.objects.select_related('forum', 'user'), pk=id)
        try:
            tlv = TopicLastVisit.objects.get(user=request.user, topic=topic)
        except TopicLastVisit.DoesNotExist:
            try:
                flv = ForumLastVisit.objects.get(user=request.user,
                        forum=topic.forum)
            except ForumLastVisit.DoesNotExist:
                return HttpResponseRedirect(topic_url)
            else:
                last_visit = flv.begin_date
        else:
            last_visit = tlv.last_visit

        posts = Post.objects.filter(topic=topic, creation_date__gt=last_visit)
        if posts:
            return _goto_post(posts[0])
        else:
            # just go to the last post in the topic
            return _goto_post(topic.last_post)

    # user isn't authenticated, just go to the topic
    return HttpResponseRedirect(topic_url)


def topic_latest(request, id):
    """
    This view shows the latest (last) post in a given topic.

    """
    topic = get_object_or_404(Topic.objects.select_related('forum', 'user'), pk=id)

    if topic.last_post:
        return _goto_post(topic.last_post)

    raise Http404


@login_required
def new_topic(request, slug):
    """
    This view handles the creation of new topics.
    """
    forum = get_object_or_404(Forum.objects.select_related(), slug=slug)

    if not perms.can_access(forum.category, request.user):
        return HttpResponseForbidden()

    if request.method == 'POST':
        form = NewTopicForm(request.user, forum, request.POST)
        if form.is_valid():
            if antispam.utils.spam_check(request, form.cleaned_data['body']):
                return HttpResponseRedirect(reverse('antispam-suspended'))

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
        if not perms.can_post(form.topic, request.user):
            return HttpResponseForbidden("You don't have permission to post in this topic.")
        if antispam.utils.spam_check(request, form.cleaned_data['body']):
            return HttpResponseForbidden(antispam.BUSTED_MESSAGE)

        post = form.save(request.user, request.META.get("REMOTE_ADDR", ""))
        post.unread = True
        post.user.user_profile = request.user.get_profile()
        post.attach_list = post.attachments.all()
        _bump_post_count(request.user)
        _update_last_visit(request.user, form.topic, datetime.datetime.now())

        return render_to_response('forums/display_post.html', {
            'post': post,
            'can_moderate': perms.can_moderate(form.topic.forum, request.user),
            'can_reply': True,
            },
            context_instance=RequestContext(request))

    return HttpResponseBadRequest("Oops, did you forget some text?");


def _goto_post(post):
    """
    Calculate what page the given post is on in its parent topic, then
    return a redirect to it.

    """
    count = post.topic.posts.filter(creation_date__lt=post.creation_date).count()
    page = count / POSTS_PER_PAGE + 1
    url = (reverse('forums-topic_index', kwargs={'id': post.topic.id}) +
        '?page=%s#p%s' % (page, post.id))
    return HttpResponseRedirect(url)


def goto_post(request, post_id):
    """
    This function calculates what page a given post is on, then redirects
    to that URL. This function is the target of get_absolute_url() for
    Post objects.
    """
    post = get_object_or_404(Post.objects.select_related(), pk=post_id)
    return _goto_post(post)


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

    can_moderate = perms.can_moderate(post.topic.forum, request.user)
    can_edit = can_moderate or request.user == post.user

    if not can_edit:
        return HttpResponseForbidden("You don't have permission to edit that post.")

    topic_name = None
    first_post = Post.objects.filter(topic=post.topic).order_by('creation_date')[0]
    if first_post.id == post.id:
        topic_name = post.topic.name

    if request.method == "POST":
        form = PostForm(request.POST, instance=post, topic_name=topic_name)
        if form.is_valid():
            if antispam.utils.spam_check(request, form.cleaned_data['body']):
                return HttpResponseRedirect(reverse('antispam-suspended'))
            post = form.save(commit=False)
            post.touch()
            post.save()
            notify_updated_post(post)

            # if we are editing a first post, save the parent topic as well
            if topic_name:
                post.topic.save()
                notify_updated_topic(post.topic)

            # Save any attachments
            form.attach_proc.save_attachments(post)

            return HttpResponseRedirect(post.get_absolute_url())
    else:
        form = PostForm(instance=post, topic_name=topic_name)

    post.user.user_profile = post.user.get_profile()

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

    if not perms.can_moderate(post.topic.forum, request.user):
        return HttpResponseForbidden("You don't have permission to delete that post.")

    delete_single_post(post)
    return HttpResponse("The post has been deleted.")


def delete_single_post(post):
    """
    This function deletes a single post. It handles the case of where
    a post is the sole post in a topic by deleting the topic also. It
    adjusts any foreign keys in Topic or Forum objects that might be pointing
    to this post before deleting the post to avoid a cascading delete.
    """
    if post.topic.post_count == 1 and post == post.topic.last_post:
        _delete_topic(post.topic)
    else:
        _delete_post(post)


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
        profile.save(content_update=False)

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

    # delete any attachments
    post.attachments.clear()

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
    parent_forum = topic.forum
    if parent_forum.last_post and parent_forum.last_post.topic == topic:
        parent_forum.last_post_pre_delete(deleting_topic=True)
        parent_forum.save()

    # delete subscriptions to this topic
    topic.subscribers.clear()
    topic.bookmarkers.clear()

    # delete all attachments
    posts = Post.objects.filter(topic=topic)
    for post in posts:
        post.attachments.clear()

    # Null out the topic's last post so we don't have a foreign key pointing
    # to a post when we delete posts.
    topic.last_post = None
    topic.save()

    # delete all posts in bulk
    posts.delete()

    # It should be safe to just delete the topic now.
    topic.delete()

    # Resync parent forum's post and topic counts
    parent_forum.sync()
    parent_forum.save()


@login_required
def new_post(request, topic_id):
    """
    This function is the view for creating a normal, non-quick reply
    to a topic.
    """
    topic = get_object_or_404(Topic.objects.select_related(), pk=topic_id)
    can_post = perms.can_post(topic, request.user)

    if can_post:
        if request.method == 'POST':
            form = PostForm(request.POST)
            if form.is_valid():
                if antispam.utils.spam_check(request, form.cleaned_data['body']):
                    return HttpResponseRedirect(reverse('antispam-suspended'))
                post = form.save(commit=False)
                post.topic = topic
                post.user = request.user
                post.user_ip = request.META.get("REMOTE_ADDR", "")
                post.save()
                notify_new_post(post)

                # Save any attachments
                form.attach_proc.save_attachments(post)

                _bump_post_count(request.user)
                _update_last_visit(request.user, topic, datetime.datetime.now())
                return HttpResponseRedirect(post.get_absolute_url())
        else:
            quote_id = request.GET.get('quote')
            if quote_id:
                quote_post = get_object_or_404(Post.objects.select_related(),
                        pk=quote_id)
                form = PostForm(initial={'body': quote_message(quote_post.user.username,
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
    if perms.can_moderate(topic.forum, request.user):
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
    if perms.can_moderate(topic.forum, request.user):
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
    if perms.can_moderate(topic.forum, request.user):
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
    if not perms.can_moderate(topic.forum, request.user):
        return HttpResponseForbidden()

    if request.method == 'POST':
        form = MoveTopicForm(request.user, request.POST)
        if form.is_valid():
            new_forum = form.cleaned_data['forums']
            old_forum = topic.forum
            _move_topic(topic, old_forum, new_forum)
            return HttpResponseRedirect(topic.get_absolute_url())
    else:
        form = MoveTopicForm(request.user)

    return render_to_response('forums/move_topic.html', {
        'forum': topic.forum,
        'topic': topic,
        'form': form,
        },
        context_instance=RequestContext(request))


@login_required
def mod_forum(request, slug):
    """
    Displays a view to allow moderators to perform various operations
    on topics in a forum in bulk. We currently support mass locking/unlocking,
    stickying and unstickying, moving, and deleting topics.
    """
    forum = get_object_or_404(Forum.objects.select_related(), slug=slug)
    if not perms.can_moderate(forum, request.user):
        return HttpResponseForbidden()

    topics = forum.topics.select_related('user', 'last_post', 'last_post__user')
    paginator = create_topic_paginator(topics)
    page_num = get_page_num(request)
    try:
        page = paginator.page(page_num)
    except InvalidPage:
        raise Http404

    # we do this for the template since it is rendered twice
    page_nav = render_to_string('forums/pagination.html', {'page': page})
    form = None

    if request.method == 'POST':
        topic_ids = request.POST.getlist('topic_ids')
        url = reverse('forums-mod_forum', kwargs={'slug':forum.slug})
        url += '?page=%s' % page_num

        if len(topic_ids):
            if request.POST.get('sticky'):
                _bulk_sticky(forum, topic_ids)
                return HttpResponseRedirect(url)
            elif request.POST.get('lock'):
                _bulk_lock(forum, topic_ids)
                return HttpResponseRedirect(url)
            elif request.POST.get('delete'):
                _bulk_delete(forum, topic_ids)
                return HttpResponseRedirect(url)
            elif request.POST.get('move'):
                form = MoveTopicForm(request.user, request.POST, hide_label=True)
                if form.is_valid():
                    _bulk_move(topic_ids, forum, form.cleaned_data['forums'])
                    return HttpResponseRedirect(url)

    if form is None:
        form = MoveTopicForm(request.user, hide_label=True)

    return render_to_response('forums/mod_forum.html', {
        'forum': forum,
        'page': page,
        'page_nav': page_nav,
        'form': form,
        },
        context_instance=RequestContext(request))


@login_required
@require_POST
def catchup_all(request):
    """
    This view marks all forums as being read.
    """
    forum_ids = Forum.objects.forum_ids_for_user(request.user)

    tlvs = TopicLastVisit.objects.filter(user=request.user,
            topic__forum__id__in=forum_ids).delete()

    now = datetime.datetime.now()
    ForumLastVisit.objects.filter(user=request.user,
            forum__in=forum_ids).update(begin_date=now, end_date=now)

    return HttpResponseRedirect(reverse('forums-index'))


@login_required
@require_POST
def forum_catchup(request, slug):
    """
    This view marks all the topics in the forum as being read.
    """
    forum = get_object_or_404(Forum.objects.select_related(), slug=slug)

    if not perms.can_access(forum.category, request.user):
        return HttpResponseForbidden()

    forum.catchup(request.user)
    return HttpResponseRedirect(forum.get_absolute_url())


@login_required
def mod_topic_split(request, id):
    """
    This view function allows moderators to split posts off to a new topic.
    """
    topic = get_object_or_404(Topic.objects.select_related(), pk=id)
    if not perms.can_moderate(topic.forum, request.user):
        return HttpResponseRedirect(topic.get_absolute_url())

    if request.method == "POST":
        form = SplitTopicForm(request.user, request.POST)
        if form.is_valid():
            if form.split_at:
                _split_topic_at(topic, form.post_ids[0],
                        form.cleaned_data['forums'],
                        form.cleaned_data['name'])
            else:
                _split_topic(topic, form.post_ids,
                        form.cleaned_data['forums'],
                        form.cleaned_data['name'])

            return HttpResponseRedirect(topic.get_absolute_url())
    else:
        form = SplitTopicForm(request.user)

    posts = topic.posts.select_related()

    return render_to_response('forums/mod_split_topic.html', {
        'forum': topic.forum,
        'topic': topic,
        'posts': posts,
        'form': form,
        },
        context_instance=RequestContext(request))


@login_required
def unread_topics(request):
    """Displays the topics with unread posts for a given user."""

    topics = get_unread_topics(request.user)

    paginator = create_topic_paginator(topics)
    page_num = get_page_num(request)
    try:
        page = paginator.page(page_num)
    except InvalidPage:
        raise Http404

    attach_topic_page_ranges(page.object_list)

    # we do this for the template since it is rendered twice
    page_nav = render_to_string('forums/pagination.html', {'page': page})

    return render_to_response('forums/topic_list.html', {
        'title': 'Topics With Unread Posts',
        'page': page,
        'page_nav': page_nav,
        'unread': True,
        },
        context_instance=RequestContext(request))


def unanswered_topics(request):
    """Displays the topics with no replies."""

    forum_ids = Forum.objects.forum_ids_for_user(request.user)
    topics = Topic.objects.filter(forum__id__in=forum_ids,
            post_count=1).select_related(
                    'forum', 'user', 'last_post', 'last_post__user')

    paginator = create_topic_paginator(topics)
    page_num = get_page_num(request)
    try:
        page = paginator.page(page_num)
    except InvalidPage:
        raise Http404

    attach_topic_page_ranges(page.object_list)

    # we do this for the template since it is rendered twice
    page_nav = render_to_string('forums/pagination.html', {'page': page})

    return render_to_response('forums/topic_list.html', {
        'title': 'Unanswered Topics',
        'page': page,
        'page_nav': page_nav,
        'unread': False,
        },
        context_instance=RequestContext(request))


def active_topics(request, num):
    """Displays the last num topics that have been posted to."""

    # sanity check num
    num = min(50, max(10, int(num)))

    # MySQL didn't do this query very well unfortunately...
    #
    #public_forum_ids = Forum.objects.public_forum_ids()
    #topics = Topic.objects.filter(forum__in=public_forum_ids).select_related(
    #            'forum', 'user', 'last_post', 'last_post__user').order_by(
    #            '-update_date')[:num]

    # Save 1 query by using forums.latest to give us a list of the most recent
    # topics; forums.latest doesn't save enough info to give us everything we
    # need so we hit the database for the rest.

    topic_ids = get_latest_topic_ids(num)
    topics = Topic.objects.filter(id__in=topic_ids).select_related(
                'forum', 'user', 'last_post', 'last_post__user').order_by(
                '-update_date')

    paginator = create_topic_paginator(topics)
    page_num = get_page_num(request)
    try:
        page = paginator.page(page_num)
    except InvalidPage:
        raise Http404

    attach_topic_page_ranges(page.object_list)

    # we do this for the template since it is rendered twice
    page_nav = render_to_string('forums/pagination.html', {'page': page})

    title = 'Last %d Active Topics' % num

    return render_to_response('forums/topic_list.html', {
        'title': title,
        'page': page,
        'page_nav': page_nav,
        'unread': False,
        },
        context_instance=RequestContext(request))


@login_required
def my_posts(request):
    """Displays a list of posts the requesting user made."""
    return _user_posts(request, request.user, request.user, 'My Posts')


@login_required
def posts_for_user(request, username):
    """Displays a list of posts by the given user.
    Only the forums that the requesting user can see are examined.
    """
    target_user = get_object_or_404(User, username=username)
    return _user_posts(request, target_user, request.user, 'Posts by %s' % username)


@login_required
def post_ip_info(request, post_id):
    """Displays information about the IP address the post was made from."""
    post = get_object_or_404(Post.objects.select_related(), pk=post_id)

    if not perms.can_moderate(post.topic.forum, request.user):
        return HttpResponseForbidden("You don't have permission for this post.")

    ip_users = sorted(set(Post.objects.filter(
        user_ip=post.user_ip).values_list('user__username', flat=True)))

    return render_to_response('forums/post_ip.html', {
        'post': post,
        'ip_users': ip_users,
        },
        context_instance=RequestContext(request))


def _user_posts(request, target_user, req_user, page_title):
    """Displays a list of posts made by the target user.
    req_user is the user trying to view the posts. Only the forums
    req_user can see are searched.
    """
    forum_ids = Forum.objects.forum_ids_for_user(req_user)
    posts = Post.objects.filter(user=target_user,
            topic__forum__id__in=forum_ids).order_by(
                    '-creation_date').select_related()

    paginator = create_post_paginator(posts)
    page_num = get_page_num(request)
    try:
        page = paginator.page(page_num)
    except InvalidPage:
        raise Http404

    # we do this for the template since it is rendered twice
    page_nav = render_to_string('forums/pagination.html', {'page': page})

    return render_to_response('forums/post_list.html', {
        'title': page_title,
        'page': page,
        'page_nav': page_nav,
        },
        context_instance=RequestContext(request))


def _bump_post_count(user):
    """
    Increments the forum_post_count for the given user.
    """
    profile = user.get_profile()
    profile.forum_post_count += 1
    profile.save(content_update=False)


def _move_topic(topic, old_forum, new_forum):
    if new_forum != old_forum:
        topic.forum = new_forum
        topic.save()
        # Have to adjust foreign keys to last_post, denormalized counts, etc.:
        old_forum.sync()
        old_forum.save()
        new_forum.sync()
        new_forum.save()


def _bulk_sticky(forum, topic_ids):
    """
    Performs a toggle on the sticky status for a given list of topic ids.
    """
    topics = Topic.objects.filter(pk__in=topic_ids)
    for topic in topics:
        if topic.forum == forum:
            topic.sticky = not topic.sticky
            topic.save()


def _bulk_lock(forum, topic_ids):
    """
    Performs a toggle on the locked status for a given list of topic ids.
    """
    topics = Topic.objects.filter(pk__in=topic_ids)
    for topic in topics:
        if topic.forum == forum:
            topic.locked = not topic.locked
            topic.save()


def _bulk_delete(forum, topic_ids):
    """
    Deletes the list of topics.
    """
    # Because we are deleting stuff, retrieve each topic one at a
    # time since we are going to be adjusting de-normalized fields
    # during deletes. In particular, we can't do this:
    #   topics = Topic.objects.filter(pk__in=topic_ids).select_related()
    #   for topic in topics:
    # since topic.forum.last_post can go stale after a delete.

    for id in topic_ids:
        try:
            topic = Topic.objects.select_related().get(pk=id)
        except Topic.DoesNotExist:
            continue
        _delete_topic(topic)


def _bulk_move(topic_ids, old_forum, new_forum):
    """
    Moves the list of topics to a new forum.
    """
    topics = Topic.objects.filter(pk__in=topic_ids).select_related()
    for topic in topics:
        if topic.forum == old_forum:
            _move_topic(topic, old_forum, new_forum)


def _update_last_visit(user, topic, visit_time):
    """
    Does the bookkeeping for the last visit status for the user to the
    topic/forum.
    """
    now = datetime.datetime.now()
    try:
        flv = ForumLastVisit.objects.get(user=user, forum=topic.forum)
    except ForumLastVisit.DoesNotExist:
        flv = ForumLastVisit(user=user, forum=topic.forum)
        flv.begin_date = now

    flv.end_date = now
    flv.save()

    if topic.update_date > flv.begin_date:
        try:
            tlv = TopicLastVisit.objects.get(user=user, topic=topic)
        except TopicLastVisit.DoesNotExist:
            tlv = TopicLastVisit(user=user, topic=topic, last_visit=datetime.datetime.min)

        if visit_time > tlv.last_visit:
            tlv.last_visit = visit_time
            tlv.save()


def _split_topic_at(topic, post_id, new_forum, new_name):
    """
    This function splits the post given by post_id and all posts that come
    after it in the given topic to a new topic in a new forum.
    It is assumed the caller has been checked for moderator rights.
    """
    post = get_object_or_404(Post, id=post_id)
    if post.topic == topic:
        post_ids = Post.objects.filter(topic=topic,
                creation_date__gte=post.creation_date).values_list('id', flat=True)
        _split_topic(topic, post_ids, new_forum, new_name)


def _split_topic(topic, post_ids, new_forum, new_name):
    """
    This function splits the posts given by the post_ids list in the
    given topic to a new topic in a new forum.
    It is assumed the caller has been checked for moderator rights.
    """
    posts = Post.objects.filter(topic=topic, id__in=post_ids)
    if len(posts) > 0:
        new_topic = Topic(forum=new_forum, name=new_name, user=posts[0].user)
        new_topic.save()
        notify_new_topic(new_topic)
        for post in posts:
            post.topic = new_topic
            post.save()

        topic.post_count_update()
        topic.save()
        new_topic.post_count_update()
        new_topic.save()
        topic.forum.sync()
        topic.forum.save()
        new_forum.sync()
        new_forum.save()
