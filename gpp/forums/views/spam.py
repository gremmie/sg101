"""
This module contains views for dealing with spam and spammers.
"""
import datetime
import logging
import textwrap

from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.contrib.auth.models import User

from comments.models import Comment
from forums.models import Post
from forums.tools import delete_user_posts
import bio.models
from core.functions import email_admins


SPAMMER_NAILED_SUBJECT = "Spammer Nailed: %s"
SPAMMER_NAILED_MSG_BODY = """
The admin/moderator user %s has just deactivated the account of %s for spam.
"""

def deactivate_spammer(user):
    """This function deactivate's the user, marks them as a spammer, then
    deletes the user's comments and forum posts. The spammer's profile is
    cleared so any spam links won't show up anymore.
    """
    user.is_active = False
    user.save()

    profile = user.get_profile()
    profile.status = bio.models.STA_SPAMMER
    profile.status_date = datetime.datetime.now()
    profile.location = ''
    profile.occupation = ''
    profile.interests = ''
    profile.profile_text = ''
    profile.signature = ''
    profile.save()

    Comment.objects.filter(user=user).delete()
    delete_user_posts(user)


def promote_stranger(user):
    """This function upgrades the user from stranger status to a regular user.
    """
    profile = user.get_profile()
    if user.is_active and profile.status == bio.models.STA_STRANGER:
        profile.status = bio.models.STA_ACTIVE
        profile.status_date = datetime.datetime.now()
        profile.save()


@login_required
def spammer(request, post_id):
    """This view allows moderators to deactivate spammer accounts."""

    post = get_object_or_404(Post.objects.select_related(), pk=post_id)
    poster = post.user
    poster_profile = poster.get_profile()

    can_moderate = request.user.is_superuser or (
            request.user in post.topic.forum.moderators.all())

    can_deactivate = (poster_profile.status == bio.models.STA_STRANGER and not
            poster.is_superuser)

    if request.method == "POST" and can_moderate and can_deactivate:
        deactivate_spammer(poster)

        email_admins(SPAMMER_NAILED_SUBJECT % poster.username,
            SPAMMER_NAILED_MSG_BODY % (
                request.user.username, poster.username))

        logging.info(textwrap.dedent("""\
            SPAMMER DEACTIVATED: %s nailed %s for spam.
            IP: %s
            Message:
            %s
            """),
            request.user.username, poster.username, post.user_ip, post.body)

        return HttpResponseRedirect(reverse('forums-spammer_nailed', args=[
            poster.id]))

    return render_to_response('forums/spammer.html', {
        'can_moderate': can_moderate,
        'can_deactivate': can_deactivate,
        'post': post,
        },
        context_instance=RequestContext(request))


@login_required
def spammer_nailed(request, spammer_id):
    """This view presents a confirmation screen that the spammer has been
    deactivated.
    """
    user = get_object_or_404(User, pk=spammer_id)
    profile = user.get_profile()

    success = not user.is_active and profile.status == bio.models.STA_SPAMMER

    return render_to_response('forums/spammer_nailed.html', {
        'spammer': user,
        'success': success,
        },
        context_instance=RequestContext(request))


@login_required
def stranger(request, post_id):
    """This view allows a forum moderator or super user to promote a user from
    stranger status to regular user.
    """
    post = get_object_or_404(Post.objects.select_related(), pk=post_id)
    poster = post.user
    poster_profile = poster.get_profile()

    can_moderate = request.user.is_superuser or (
            request.user in post.topic.forum.moderators.all())

    can_promote = poster_profile.status == bio.models.STA_STRANGER

    if request.method == "POST" and can_moderate and can_promote:
        promote_stranger(poster)

        logging.info("STRANGER PROMOTED: %s promoted %s.",
            request.user.username, poster.username)

        return HttpResponseRedirect(post.get_absolute_url())

    return render_to_response('forums/stranger.html', {
        'can_moderate': can_moderate,
        'can_promote': can_promote,
        'post': post,
        },
        context_instance=RequestContext(request))
