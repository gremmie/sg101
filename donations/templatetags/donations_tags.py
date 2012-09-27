"""
Template tags for the donations application.

"""
from django import template

from donations.models import Donation


register = template.Library()


@register.inclusion_tag('donations/monthly_goal_tag.html')
def monthly_goal():
    return {
        'pct': Donation.objects.monthly_goal_pct()
    }
