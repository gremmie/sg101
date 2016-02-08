"""
Template tags for the POTD application.
"""
from django import template
from potd.models import Current

register = template.Library()

@register.simple_tag(takes_context=True)
def photo_of_the_day(context):
    potd = Current.objects.get_current_photo()
    context['potd'] = potd
    template_name = ('potd/v3/potd_block.html'
            if 'V3_DESIGN' in context else 'potd/potd_block.html')

    t = template.loader.get_template(template_name)
    return t.render(context)
