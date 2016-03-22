"""Template tags for the contests application.

"""

from django import template

from contests.models import Contest


register = template.Library()


@register.simple_tag(takes_context=True)
def latest_contests_block(context):
    contests = Contest.public_objects.get_current_contests()
    template_name = ('contests/v3/latest_contests_block_tag.html'
            if 'V3_DESIGN' in context else 'contests/latest_contests_block_tag.html')
    t = template.loader.get_template(template_name)

    with context.push():
        context['contests'] = contests
        return t.render(context)
