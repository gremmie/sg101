"""
Template tags to generate <link> and <script> tags for 3rd party Javascript scripts.
"""
from django import template
from django.conf import settings

register = template.Library()

@register.inclusion_tag('core/script_tags.html')
def script_tags(libraries):
    css = []
    js = []
    for library in libraries.split():
        if library in settings.GPP_THIRD_PARTY_CSS:
            for path in settings.GPP_THIRD_PARTY_CSS[library]:
                local = not path.startswith('http')
                css.append((local, path))

        if library in settings.GPP_THIRD_PARTY_JS:
            for path in settings.GPP_THIRD_PARTY_JS[library]:
                local = not path.startswith('http')
                js.append((local, path))

    return {
        'css_sources': css,
        'js_sources': js,
    }


@register.inclusion_tag('core/css_tags.html')
def css_tags(libraries):
    css = []
    for library in libraries.split():
        if library in settings.GPP_THIRD_PARTY_CSS:
            for path in settings.GPP_THIRD_PARTY_CSS[library]:
                local = not path.startswith('http')
                css.append((local, path))

    return {
        'css_sources': css,
    }


@register.inclusion_tag('core/js_tags.html')
def js_tags(libraries):
    js = []
    for library in libraries.split():
        if library in settings.GPP_THIRD_PARTY_JS:
            for path in settings.GPP_THIRD_PARTY_JS[library]:
                local = not path.startswith('http')
                js.append((local, path))

    return {
        'js_sources': js,
    }
