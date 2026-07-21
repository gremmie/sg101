"""
Template tags for the messages application.

"""
from django import template
from django.urls import reverse
from django.utils.http import urlquote

from messages.models import Message


register = template.Library()

@register.simple_tag(takes_context=True)
def unread_messages(context):
    user = context['user']
    if user.is_authenticated:
        unread_count = Message.objects.unread_count(user)
    else:
        unread_count = None
    context['unread_count'] = unread_count
    template_name = ('messages/v3/unread_messages_tag.html'
            if 'V3_DESIGN' in context else 'messages/unread_messages_tag.html')
    t = template.loader.get_template(template_name)
    return t.render(context.flatten())


@register.simple_tag
def send_pm_url(username):
    """Returns the URL to send a PM to a given username"""
    return reverse('messages-compose') + '?to={}'.format(urlquote(username))
