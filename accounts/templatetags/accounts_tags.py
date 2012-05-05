"""
Template tags for the accounts applications.

"""
from django import template

from accounts.stats import get_user_stats


register = template.Library()


@register.inclusion_tag('accounts/user_stats_tag.html')
def user_stats():
    """
    This tag renders the total number of site users and a list of new users.

    """
    num_users, new_users = get_user_stats()
    return {'num_users': num_users, 'new_users': new_users}
