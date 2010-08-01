"""This module handles the subscriptions of users to forum topics."""
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.sites.models import Site
from django.core.paginator import InvalidPage
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.http import Http404
from django.template.loader import render_to_string
from django.shortcuts import get_object_or_404
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.views.decorators.http import require_POST

from forums.models import Topic
from core.functions import send_mail
from core.paginator import DiggPaginator


def notify_topic_subscribers(post):
    """The argument post is a newly created post. Send out an email
    notification to all subscribers of the post's parent Topic."""

    topic = post.topic
    recipients = topic.subscribers.exclude(
            id=post.user.id).values_list('email', flat=True)

    if recipients:
        site = Site.objects.get_current()
        subject = "[%s] Topic Reply: %s" % (site.name, topic.name)
        url_prefix = "http://%s" % site.domain
        post_url = url_prefix + post.get_absolute_url()
        unsubscribe_url = url_prefix + reverse("forums-manage_subscriptions")
        msg = render_to_string("forums/topic_notify_email.txt", {
                'poster': post.user.username,
                'topic_name': topic.name,
                'message': post.body,
                'post_url': post_url,
                'unsubscribe_url': unsubscribe_url,
                })
        for recipient in recipients:
            send_mail(subject, msg, settings.DEFAULT_FROM_EMAIL, [recipient])


@login_required
@require_POST
def subscribe_topic(request, topic_id):
    """Subscribe the user to the requested topic."""
    topic = get_object_or_404(Topic.objects.select_related(), id=topic_id)
    if topic.forum.category.can_access(request.user):
        topic.subscribers.add(request.user)
        return HttpResponseRedirect(
            reverse("forums-subscription_status", args=[topic.id]))
    raise Http404   # TODO return HttpResponseForbidden instead


@login_required
@require_POST
def unsubscribe_topic(request, topic_id):
    """Unsubscribe the user to the requested topic."""
    topic = get_object_or_404(Topic, id=topic_id)
    topic.subscribers.remove(request.user)
    return HttpResponseRedirect(
        reverse("forums-subscription_status", args=[topic.id]))


@login_required
def subscription_status(request, topic_id):
    """Display the subscription status for the given topic."""
    topic = get_object_or_404(Topic.objects.select_related(), id=topic_id)
    is_subscribed = request.user in topic.subscribers.all()
    return render_to_response('forums/subscription_status.html', {
        'topic': topic,
        'is_subscribed': is_subscribed,
        },
        context_instance=RequestContext(request))


@login_required
def manage_subscriptions(request):
    """Display a user's topic subscriptions, and allow them to be deleted."""

    user = request.user
    if request.method == "POST":
        if request.POST.get('delete_all'):
            user.subscriptions.clear()
        else:
            delete_ids = request.POST.getlist('delete_ids')
            try:
                delete_ids = [int(id) for id in delete_ids]
            except ValueError:
                raise Http404
            for topic in user.subscriptions.filter(id__in=delete_ids):
                user.subscriptions.remove(topic)

        page_num = request.POST.get('page', 1)
    else:
        page_num = request.GET.get('page', 1)

    topics = user.subscriptions.select_related().order_by('-update_date')
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
        'page_title': 'Topic Subscriptions',
        'description': 'The forum topics you are currently subscribed to are listed below.',
        'page': page,
        },
        context_instance=RequestContext(request))
