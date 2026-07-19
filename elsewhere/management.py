from django.db.models.signals import post_migrate
from django.dispatch import receiver

from elsewhere.default_list import *
from elsewhere.models import SocialNetwork, InstantMessenger

# this function will fill the database with default data (stored in default_lists.py)


@receiver(post_migrate)
def fill_db(sender=None, **kwargs):
    for item in default_social_networks: # fill social networks
        if 'identifier' in item:
            ident = item['identifier']
        else:
            ident = ''

        SocialNetwork.objects.get_or_create(name=item['name'], defaults={
            'url': item['url'],
            'identifier': ident,
            'icon': item['icon']
        })

    for item in default_im_networks: # fill IM networks
        if 'identifier' in item:
            ident = item['identifier']
        else:
            ident = ''

        InstantMessenger.objects.get_or_create(name=item['name'], defaults={
            'url': item['url'],
            'identifier': ident,
            'icon': item['icon']
        })
