"""Template tags for the IRC application."""

from django import template

from irc.channel import get_users

register = template.Library()

@register.simple_tag(takes_context=True)
def irc_status(context):
    template_name = ('irc/v3/irc_block.html'
            if 'V3_DESIGN' in context else 'irc/irc_block.html')
    context['nicks'] = get_users()
    t = template.loader.get_template(template_name)
    return t.render(context)
