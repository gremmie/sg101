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


@register.inclusion_tag('donations/top_donors_tag.html')
def top_donors(n=10):
    return {
        'top_donors': Donation.objects.top_donors(n)
    }
