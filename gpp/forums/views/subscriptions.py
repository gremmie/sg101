"""This module handles the subscriptions of users to forum topics."""
import datetime

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

from forums.models import Topic, TopicLastVisit, Subscription
from core.functions import send_mail
from core.paginator import DiggPaginator


# This constant is the minimum amount of time a user will be
# notified of new posts in a topic. Currently it is set to 1 day.
# Thus a user will be notified at most once per day of new posts.
TOPIC_NOTIFY_DELAY = datetime.timedelta(days=1)


def notify_topic_subscribers(post):
    """
    The argument post is a newly created post. Send out an email
    notification to all subscribers of the post's parent Topic.
    The emails are throttled such that unless the user visits the topic,
    only 1 email will be sent per TOPIC_NOTIFY_DELAY period.
    Visiting the topic will reset this delay.

    """
    #TODO: consider moving this function of the HTTP request/response cycle.

    topic = post.topic
    subscriptions = Subscription.objects.filter(topic=post.topic).exclude(
            user=post.user).select_related()

    if not subscriptions:
        return

    subscriber_ids = [sub.user.id for sub in subscriptions]
    tlvs = dict(TopicLastVisit.objects.filter(topic=topic,
            user__in=subscriber_ids).values_list('user', 'last_visit'))

    recipients = []
    for sub in subscriptions:
        if (sub.notify_date is None or
            post.creation_date - sub.notify_date > TOPIC_NOTIFY_DELAY or
            tlvs.get(sub.user.id, datetime.datetime.min) > sub.notify_date):

            recipients.append(sub.user.email)
            sub.notify_date = post.creation_date
            sub.save()

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
        sub = Subscription(topic=topic, user=request.user)
        sub.save()
        return HttpResponseRedirect(
            reverse("forums-subscription_status", args=[topic.id]))
    raise Http404   # TODO return HttpResponseForbidden instead


@login_required
@require_POST
def unsubscribe_topic(request, topic_id):
    """Unsubscribe the user to the requested topic."""
    topic = get_object_or_404(Topic, id=topic_id)
    try:
        sub = Subscription.objects.get(topic=topic, user=request.user)
    except Subscription.DoesNotExist:
        pass
    else:
        sub.delete()
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
            Subscription.objects.filter(user=user).delete()
        else:
            delete_ids = request.POST.getlist('delete_ids')
            try:
                delete_ids = [int(id) for id in delete_ids]
            except ValueError:
                raise Http404

            Subscription.objects.filter(user=user, topic__in=delete_ids).delete()

        return HttpResponseRedirect(reverse("forums-manage_subscriptions"))

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
