"""
Template tags for the messages application.

"""
from django import template
from django.core.urlresolvers import reverse
from django.utils.http import urlquote

from messages.models import Message


register = template.Library()

@register.inclusion_tag('messages/unread_messages_tag.html')
def unread_messages(user):
    unread_count = Message.objects.unread_count(user)
    return {'unread_count': unread_count}


@register.simple_tag
def send_pm_url(username):
    """Returns the URL to send a PM to a given username"""
    return reverse('messages-compose') + '?to={}'.format(urlquote(username))
