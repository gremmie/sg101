"""
Template tags for the messages application.
"""
from django import template
from django.core.urlresolvers import reverse

from messages.models import Message


register = template.Library()

@register.simple_tag
def unread_messages(user):
    inbox_url = reverse('messages-inbox')
    unread_count = Message.objects.unread_count(user)
    if unread_count == 0:
        link_text = u"Private Messages"
    elif unread_count == 1:
        link_text = u"1 New Message"
    else:
        link_text = u"%s New Messages" % unread_count
    return u'<a href="%s">%s</a>' % (inbox_url, link_text)


# vim: ts=4 sw=4
