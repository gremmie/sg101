"""
Template tags for the elsewhere application. 
"""
from django import template
from django.conf import settings

register = template.Library()


@register.inclusion_tag('bio/elsewhere_links.html', takes_context=True)
def elsewhere_links(context, user):
    return {
        'social_nets': user.social_network_profiles.all(),
        'ims': user.instant_messenger_profiles.all(),
        'websites': user.website_profiles.all(),
        'MEDIA_URL': context['MEDIA_URL'],
    }
