"""Template tags for the countdown application."""
import datetime

from django import template

from countdown.models import Event


register = template.Library()


@register.simple_tag(takes_context=True)
def countdown_events(context):
    """This tag renders a countdown to upcoming events."""
    now = datetime.datetime.now()

    results = []
    for event in Event.active_objects.all():
        delta = event.event_date.date() - now.date()
        if delta.days >= 0:
            results.append((delta.days, event))

    template_name = ('countdown/v3/countdown_tag.html'
            if 'V3_DESIGN' in context else 'countdown/countdown_tag.html')
    t = template.loader.get_template(template_name)
    with context.push():
        context['events'] = results
        return t.render(context.flatten())
