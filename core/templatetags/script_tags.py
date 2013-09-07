"""
Template tags to generate <link> and <script> tags for 3rd party Javascript scripts.
"""
from django import template
from django.conf import settings

register = template.Library()

@register.simple_tag
def script_tags(libraries):
    s = ''
    for library in libraries.split():
        if library in settings.GPP_THIRD_PARTY_CSS:
            for path in settings.GPP_THIRD_PARTY_CSS[library]:
                prefix = ''
                if not path.startswith('http'):
                    prefix = settings.STATIC_URL
                s += '<link rel="stylesheet" href="%s%s" />' % (prefix, path)

        if library in settings.GPP_THIRD_PARTY_JS:
            for path in settings.GPP_THIRD_PARTY_JS[library]:
                prefix = ''
                if not path.startswith('http'):
                    prefix = settings.STATIC_URL
                s += '<script src="%s%s"></script>' % (prefix, path)

    return s
