"""Seed the networks members actually use, and retire the ones nobody picked.

These rows used to be created by a post_migrate receiver that re-ran on every
migrate in every environment. They are ordinary data and belong in a migration
like the rest of this project's seeded data.

The list is also shorter than the one the receiver used. Of 57 social networks
offered, 42 had never been chosen by a single member, most of them services
that no longer exist, and of 6 instant messengers 1 was never chosen; they are
removed here. Nothing in use is touched, and the delete is guarded on the
network having no profile rows rather than on the list alone, so a network
someone picked between this being written and being run survives it.

The instant messengers that remain are all defunct services, and no new ones
can be added, but members' existing entries have to keep rendering: a profile
row whose network is gone is what takes a page down.

Reversing restores the URL templates as they were but does not re-create the
retired networks. Nothing a profile row points at is ever deleted, in either
direction.

"""
import logging

from django.core.cache import cache
from django.db import migrations

logger = logging.getLogger(__name__)

# Cache keys are spelled out rather than imported: a migration is a snapshot,
# and must not follow the app's constants as they change.
SN_CACHE_KEY = 'elsewhere_sn_data'
IM_CACHE_KEY = 'elsewhere_im_data'

# slug, name, url, identifier, icon
SOCIAL_NETWORKS = [
    ('facebook', 'Facebook', 'https://www.facebook.com/profile.php?id=%s', 'User ID', 'facebook.png'),
    ('flickr', 'Flickr', 'https://www.flickr.com/photos/%s/', 'Flickr Alias', 'flickr.png'),
    ('foursquare', 'foursquare', 'https://foursquare.com/user?uid=%s', 'User ID', 'foursquare.png'),
    ('github', 'GitHub', 'https://github.com/%s', 'Username', 'github.png'),
    ('goodreads', 'GoodReads', 'https://www.goodreads.com/user/show/%s', 'User ID', 'goodreads.png'),
    ('lastfm', 'Last.fm', 'https://www.last.fm/user/%s', 'Username', 'lastfm.png'),
    ('linkedin', 'LinkedIn', 'https://www.linkedin.com/in/%s', 'Full Name (without spaces)', 'linkedin.png'),
    ('multiply', 'Multiply', 'https://%s.multiply.com', 'Username', 'multiply.png'),
    ('myspace', 'MySpace', 'https://myspace.com/%s', 'Username', 'myspace.png'),
    ('pandora', 'Pandora', 'https://www.pandora.com/profile/%s', 'Username', 'pandora.png'),
    ('redbubble', 'RedBubble', 'https://www.redbubble.com/people/%s', 'Username', 'redbubble.png'),
    ('reddit', 'Reddit', 'https://www.reddit.com/user/%s', 'Username', 'reddit.png'),
    ('tumblr', 'Tumblr', 'https://%s.tumblr.com', 'Username', 'tumblr.png'),
    ('twitter', 'Twitter', 'https://x.com/%s', 'Username', 'twitter.png'),
    ('youtube', 'YouTube', 'https://www.youtube.com/user/%s', 'Username', 'youtube.png'),
]

INSTANT_MESSENGERS = [
    ('aim', 'AIM', 'aim:goim?screenname=%s', '', 'aim.png'),
    ('gtalk', 'GTalk', 'gtalk:chat?jid=%s', '', 'gtalk.png'),
    ('msn', 'MSN', 'msnim:chat?contact=%s', '', 'msn.png'),
    ('skype', 'Skype', 'skype:%s?chat', '', 'skype.png'),
    ('y', 'Y!', 'ymsgr:sendim?%s', '', 'yahoo.png'),
]

# What the surviving networks pointed at before, so a reverse puts them back.
PREVIOUS_URLS = {
    'facebook': 'http://www.facebook.com/profile.php?id=%s',
    'flickr': 'http://www.flickr.com/photos/%s/',
    'foursquare': 'http://playfoursquare.com/user?uid=%s',
    'github': 'http://github.com/%s',
    'goodreads': 'http://www.goodreads.com/user/show/%s',
    'lastfm': 'http://www.last.fm/user/%s',
    'linkedin': 'http://www.linkedin.com/in/%s',
    'multiply': 'http://%s.multiply.com',
    'myspace': 'http://www.myspace.com/%s',
    'pandora': 'http://pandora.com/people/%s',
    'redbubble': 'http://www.redbubble.com/people/%s',
    'reddit': 'http://reddit.com/user/%s',
    'tumblr': 'http://%s.tumblr.com',
    'twitter': 'http://twitter.com/%s',
    'youtube': 'http://www.youtube.com/user/%s',
}


def _seed(model, rows):
    for slug, name, url, identifier, icon in rows:
        model.objects.update_or_create(slug=slug, defaults={
            'name': name,
            'url': url,
            'identifier': identifier,
            'icon': icon,
        })


def _bust_caches():
    # Redis in production, so the running site picks the new list up at once
    # rather than at the end of the 24 hour entry.
    cache.delete(SN_CACHE_KEY)
    cache.delete(IM_CACHE_KEY)


def _prune(model, profile_model, rows):
    """Drop the networks nobody chose, and only those.

    Guarded on the profile rows rather than on the list alone: a network picked
    between this being written and being run is kept, because deleting one a
    row points at takes that member's profile page down.

    A network kept that way is reported, because its icon file was removed
    along with the ones it was grouped with, and a missing icon is not a
    missing image -- ManifestStaticFilesStorage raises on it, so the page 500s.
    Restore the named file from git history and the entry renders again.

    """
    kept = {row[0] for row in rows}
    in_use = set(profile_model.objects.values_list('network_id', flat=True)
                 .distinct())

    rescued = model.objects.exclude(slug__in=kept).filter(slug__in=in_use)
    for network in rescued:
        logger.warning(
            '%s was retired from the seed list but a member is using it, so '
            'it has been kept. Restore elsewhere/static/elsewhere/%s or that '
            'profile page will fail to render.', network.slug, network.icon)

    model.objects.exclude(slug__in=kept | in_use).delete()


def seed_networks(apps, schema_editor):
    social = apps.get_model('elsewhere', 'SocialNetwork')
    messenger = apps.get_model('elsewhere', 'InstantMessenger')
    social_profile = apps.get_model('elsewhere', 'SocialNetworkProfile')
    messenger_profile = apps.get_model('elsewhere', 'InstantMessengerProfile')

    _seed(social, SOCIAL_NETWORKS)
    _seed(messenger, INSTANT_MESSENGERS)

    _prune(social, social_profile, SOCIAL_NETWORKS)
    _prune(messenger, messenger_profile, INSTANT_MESSENGERS)

    _bust_caches()


def restore_urls(apps, schema_editor):
    """Put the previous URL templates back. Retired networks stay retired."""
    for model_name in ('SocialNetwork', 'InstantMessenger'):
        model = apps.get_model('elsewhere', model_name)
        for network in model.objects.filter(slug__in=PREVIOUS_URLS):
            network.url = PREVIOUS_URLS[network.slug]
            network.save(update_fields=['url'])

    _bust_caches()


class Migration(migrations.Migration):

    dependencies = [
        ('elsewhere', '0003_network_slug'),
    ]

    operations = [
        migrations.RunPython(seed_networks, restore_urls),
    ]
