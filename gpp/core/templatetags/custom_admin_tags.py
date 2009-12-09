"""
Custom template tags for the admin.
"""
from django import template
from django.db.models import Q

from bio.models import UserProfileFlag
from comments.models import CommentFlag
from downloads.models import Download
from forums.models import FlaggedPost
from gcalendar.models import Event
from news.models import PendingStory
from weblinks.models import Link


register = template.Library()


@register.inclusion_tag('core/admin_dashboard.html')
def admin_dashboard(user):
    """
    This tag is used in the admin to create a dashboard
    of pending content that an admin must approve.
    """
    flagged_profiles = UserProfileFlag.objects.count()
    flagged_comments = CommentFlag.objects.count()
    new_downloads = Download.objects.filter(is_public=False).count()
    flagged_posts = FlaggedPost.objects.count()
    event_requests = Event.objects.filter(
                Q(status=Event.NEW) | 
                Q(status=Event.EDIT_REQ) | 
                Q(status=Event.DEL_REQ)).count()
    new_stories = PendingStory.objects.count()
    new_links = Link.objects.filter(is_public=False).count()

    return {
        'user': user,
        'flagged_profiles': flagged_profiles,
        'flagged_comments': flagged_comments,
        'new_downloads': new_downloads,
        'flagged_posts': flagged_posts,
        'event_requests': event_requests,
        'new_stories': new_stories,
        'new_links': new_links,
        }
