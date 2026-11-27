"""
Template tags for the POTD application.
"""
from django import template
from potd.models import Current

register = template.Library()

@register.simple_tag(takes_context=True)
def photo_of_the_day(context):
    potd = Current.objects.get_current_photo()
    t = template.loader.get_template('potd/v3/potd_block.html')
    with context.push():
        context['potd'] = potd
        return t.render(context.flatten())
