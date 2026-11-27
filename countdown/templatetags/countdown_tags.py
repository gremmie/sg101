"""Template tags for the countdown application."""

from django import template
from django.utils import timezone

from countdown.models import Event


register = template.Library()


@register.simple_tag(takes_context=True)
def countdown_events(context):
    """This tag renders a countdown to upcoming events."""
    now = timezone.now()

    results = []
    for event in Event.active_objects.all():
        delta = event.event_date.date() - now.date()
        if delta.days >= 0:
            results.append((delta.days, event))

    t = template.loader.get_template('countdown/v3/countdown_tag.html')
    with context.push():
        context['events'] = results
        return t.render(context.flatten())
