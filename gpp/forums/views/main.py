"""
Views for the forums application.
"""
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
from django.utils.text import wrap
from django.db.models import F

from core.paginator import DiggPaginator
from core.functions import email_admins
from forums.models import Forum, Topic, Post, FlaggedPost, TopicLastVisit, \
        ForumLastVisit, Attachment
from forums.forms import NewTopicForm, NewPostForm, PostForm, MoveTopicForm, \
        SplitTopicForm
from forums.unread import get_forum_unread_status, get_topic_unread_status, \
        get_post_unread_status, get_unread_topics

from bio.models import UserProfile
import antispam
import antispam.utils
from forums.attachments import AttachmentProcessor

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

    if not forum.category.can_access(request.user):
        return HttpResponseForbidden()

    feed = None
    if not forum.category.groups.all():
        feed = {
            'name': '%s Forum' % forum.name,
            'feed': FORUM_FEED % forum.slug,
        }

    topics = forum.topics.select_related('user', 'last_post', 'last_post__user')
    get_topic_unread_status(forum, topics, request.user)

    paginator = create_topic_paginator(topics)
    page_num = get_page_num(request)
    try:
        page = paginator.page(page_num)
    except InvalidPage:
        raise Http404

    attach_topic_page_ranges(page.object_list)

    # we do this for the template since it is rendered twice
    page_nav = render_to_string('forums/pagination.html', {'page': page})

    can_moderate = _can_moderate(forum, request.user)

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

    if not topic.forum.category.can_access(request.user):
        return HttpResponseForbidden()

    topic.view_count = F('view_count') + 1
    topic.save(force_update=True)

    posts = topic.posts.select_related()

    paginator = create_post_paginator(posts)
    page_num = get_page_num(request)
    try:
        page = paginator.page(page_num)
    except InvalidPage:
        raise Http404
    get_post_unread_status(topic, page.object_list, request.user)

    # Attach user profiles to each post to avoid using get_user_profile() in
    # the template.
    users = set(post.user.id for post in page.object_list)

    profiles = UserProfile.objects.filter(user__id__in=users).select_related()
    user_profiles = dict((profile.user.id, profile) for profile in profiles)

    for post in page.object_list:
        post.user_profile = user_profiles[post.user.id]
        post.attach_list = []

    # Attach any attachments
    post_ids = [post.pk for post in page.object_list]
    attachments = Attachment.objects.filter(post__in=post_ids).select_related(
            'embed').order_by('order')

    post_dict = dict((post.pk, post) for post in page.object_list)
    for item in attachments:
        post_dict[item.post.id].attach_list.append(item.embed)

    last_page = page_num == paginator.num_pages

    if request.user.is_authenticated() and last_page:
        _update_last_visit(request.user, topic)

    # we do this for the template since it is rendered twice
    page_nav = render_to_string('forums/pagination.html', {'page': page})

    can_moderate = _can_moderate(topic.forum, request.user)

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
        if not _can_post_in_topic(form.topic, request.user):
            return HttpResponseForbidden("You don't have permission to post in this topic.")
        if antispam.utils.spam_check(request, form.cleaned_data['body']):
            return HttpResponseForbidden(antispam.BUSTED_MESSAGE)

        post = form.save(request.user, request.META.get("REMOTE_ADDR", ""))
        post.unread = True
        post.user_profile = request.user.get_profile()
        post.attach_list = post.attachments.all()
        _bump_post_count(request.user)
        _update_last_visit(request.user, form.topic)

        return render_to_response('forums/display_post.html', {
            'post': post,
            'can_moderate': _can_moderate(form.topic.forum, request.user),
            'can_reply': True,
            },
            context_instance=RequestContext(request))

    return HttpResponseBadRequest("Oops, did you forget some text?");


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
            if antispam.utils.spam_check(request, form.cleaned_data['body']):
                return HttpResponseRedirect(reverse('antispam-suspended'))
            post = form.save(commit=False)
            post.touch()
            post.save()

            # Save any attachments
            form.attach_proc.save_attachments(post)

            return HttpResponseRedirect(post.get_absolute_url())
    else:
        form = PostForm(instance=post)

    post.user_profile = request.user.get_profile()

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
    if topic.forum.last_post and topic.forum.last_post.topic == topic:
        topic.forum.last_post_pre_delete()
        topic.forum.save()

    # delete subscriptions to this topic
    topic.subscribers.clear()
    topic.bookmarkers.clear()

    # delete all attachments
    posts = Post.objects.filter(topic=topic)
    for post in posts:
        post.attachments.clear()

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
                if antispam.utils.spam_check(request, form.cleaned_data['body']):
                    return HttpResponseRedirect(reverse('antispam-suspended'))
                post = form.save(commit=False)
                post.topic = topic
                post.user = request.user
                post.user_ip = request.META.get("REMOTE_ADDR", "")
                post.save()

                # Save any attachments
                form.attach_proc.save_attachments(post)

                _bump_post_count(request.user)
                _update_last_visit(request.user, topic)
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
    if not _can_moderate(forum, request.user):
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
def forum_catchup(request, slug):
    """
    This view marks all the topics in the forum as being read.
    """
    forum = get_object_or_404(Forum.objects.select_related(), slug=slug)

    if not forum.category.can_access(request.user):
        return HttpResponseForbidden()

    forum.catchup(request.user)
    return HttpResponseRedirect(forum.get_absolute_url())


@login_required
def mod_topic_split(request, id):
    """
    This view function allows moderators to split posts off to a new topic.
    """
    topic = get_object_or_404(Topic.objects.select_related(), pk=id)
    if not _can_moderate(topic.forum, request.user):
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

    if not _can_moderate(post.topic.forum, request.user):
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


def _update_last_visit(user, topic):
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
            tlv = TopicLastVisit(user=user, topic=topic)

        tlv.touch()
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
