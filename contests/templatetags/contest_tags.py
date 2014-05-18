"""Template tags for the contests application.

"""

from django import template

from contests.models import Contest


register = template.Library()


@register.inclusion_tag('contests/latest_contests_block_tag.html')
def latest_contests_block():
    contests = Contest.public_objects.get_current_contests()
    return {'contests': contests}
