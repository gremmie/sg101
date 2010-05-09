"""
This module contains views for dealing with spam and spammers.
"""
import datetime

from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
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
    deletes the user's comments and forum posts.
    """
    user.is_active = False
    user.save()

    profile = user.get_profile()
    profile.status = bio.models.STA_SPAMMER
    profile.status_date = datetime.datetime.now()
    profile.save()

    Comment.objects.filter(user=user).delete()
    delete_user_posts(user)


@login_required
def spammer(request, post_id):
    """This view allows moderators to deactivate spammer accounts."""

    post = get_object_or_404(Post.objects.select_related(), pk=post_id)

    can_moderate = request.user.is_superuser or (
            request.user in post.topic.forum.moderators.all())

    if request.method == "POST":
        if can_moderate:
            deactivate_spammer(post.user)

            email_admins(SPAMMER_NAILED_SUBJECT % post.user.username, 
                SPAMMER_NAILED_MSG_BODY % (
                    request.user.username, post.user.username))

            return HttpResponseRedirect(reverse('forums-spammer_nailed', args=[
                post.user.id]))

    return render_to_response('forums/spammer.html', {
        'can_moderate': can_moderate,
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
