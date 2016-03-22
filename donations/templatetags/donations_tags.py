"""
Template tags for the donations application.

"""
from django import template

from donations.models import Donation


register = template.Library()


@register.simple_tag(takes_context=True)
def monthly_goal(context):
    template_name = ('donations/v3/monthly_goal_tag.html'
            if 'V3_DESIGN' in context else 'donations/monthly_goal_tag.html')
    t = template.loader.get_template(template_name)

    with context.push():
        context['pct'] = Donation.objects.monthly_goal_pct()
        return t.render(context)


@register.inclusion_tag('donations/top_donors_tag.html')
def top_donors(n=10):
    return {
        'top_donors': Donation.objects.top_donors(n)
    }
