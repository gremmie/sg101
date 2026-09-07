import logging

from django import forms
from django.db import models
from django.db.models.fields import BLANK_CHOICE_DASH
from django.core.cache import cache
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

logger = logging.getLogger(__name__)

SN_CACHE_KEY = 'elsewhere_sn_data'
IM_CACHE_KEY = 'elsewhere_im_data'


class Network(models.Model):
    """ Model for storing networks. """

    name = models.CharField(max_length=100)
    # The key profiles are stored against. It is 16 characters because that is
    # the width of the network_id columns that hold it.
    slug = models.SlugField(max_length=16, unique=True)
    url = models.URLField()
    identifier = models.CharField(max_length=100)
    icon = models.CharField(max_length=100, blank=True)

    class Meta:
        abstract = True

    def __str__(self):
        return self.name

class SocialNetwork(Network):
    class Meta:
        verbose_name_plural = 'social networks'

    def save(self, *args, **kwargs):
        cache.delete(SN_CACHE_KEY)
        super(SocialNetwork, self).save(*args, **kwargs)

class InstantMessenger(Network):
    class Meta:
        verbose_name_plural = 'instant messanger networks'

    def save(self, *args, **kwargs):
        cache.delete(IM_CACHE_KEY)
        super(InstantMessenger, self).save(*args, **kwargs)

# The following makes the social / IM networks data act as dicts.

def get_social_network_data():
    data = cache.get(SN_CACHE_KEY)

    if not data:
        data = {}
        for network in SocialNetwork.objects.order_by('name').iterator():
            data[network.slug] = {
                'id': network.slug,
                'name': network.name,
                'url': network.url,
                'identifier': network.identifier,
                'icon': network.icon
            }
        cache.set(SN_CACHE_KEY, data, 60*60*24)

    return data

def get_instant_messanger_data():
    data = cache.get(IM_CACHE_KEY)

    if not data:
        data = {}
        for network in InstantMessenger.objects.order_by('name').iterator():
            data[network.slug] = {
                'id': network.slug,
                'name': network.name,
                'url': network.url,
                'icon': network.icon
            }
        cache.set(IM_CACHE_KEY, data, 60*60*24)

    return data

class ProfileManager:
    """ Handle raw data for dicts of profiles."""

    def _get_choices(self):
        """ List of choices for profile select fields. """
        return [(props['id'], props['name']) for props in self.data.values()]
    choices = property(_get_choices)

# The managers hold no data of their own. Saving a network clears the cache
# entry, and anything memoized here would outlive that and go on serving the
# list the process happened to read first.

class SocialNetworkManager(ProfileManager):
    def _get_data(self):
        return get_social_network_data()
    data = property(_get_data)
sn_manager = SocialNetworkManager()

class InstantMessengerManager(ProfileManager):
    def _get_data(self):
        return get_instant_messanger_data()
    data = property(_get_data)
im_manager = InstantMessengerManager()

class Profile(models.Model):
    """ Common profile model pieces. """
    data_manager = None

    date_added = models.DateTimeField(_('date added'), auto_now_add=True)
    date_verified = models.DateTimeField(_('date verified'), default=timezone.now)
    is_verified = models.BooleanField(default=False)

    class Meta:
        abstract = True

    def _get_data_item(self):
        # Find profile data for this profile id. Nothing enforces that the
        # stored slug still names a network, so a row can outlive one; when
        # that happens the entry is skipped rather than taking the page down.
        try:
            return self.data_manager.data[self.network_id]
        except KeyError:
            logger.warning('no network registered under the slug %r '
                           '(profile %s)', self.network_id, self.pk)
            return None
    data_item = property(_get_data_item)

    def _get_name(self):
        # Profile display name
        item = self.data_item
        return item['name'] if item else ''
    name = property(_get_name)

    def _get_url(self):
        # Profile URL with username
        item = self.data_item
        return item['url'] % self.username if item else ''
    url = property(_get_url)

    def _get_icon_name(self):
        # Icon name
        item = self.data_item
        return item['icon'] if item else ''
    icon_name = property(_get_icon_name)

class SocialNetworkProfile(Profile):
    data_manager = sn_manager

    user = models.ForeignKey(User, db_index=True,
                             related_name='social_network_profiles',
                             on_delete=models.CASCADE)
    # The valid networks are dynamic data (loaded via the post_migrate hook), so
    # the choices live on the form, not frozen onto the model field at import.
    network_id = models.CharField(max_length=16, db_index=True)
    username = models.CharField(max_length=64)

    def __str__(self):
        return self.network_id

class SocialNetworkForm(forms.ModelForm):
    network_id = forms.ChoiceField()

    class Meta:
        model = SocialNetworkProfile
        fields = ('network_id', 'username')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Populate the network choices from the live data each time the form is
        # built. They can't be set at class-definition time: this module is
        # imported before the post_migrate hook fills the network tables, so on a
        # fresh database the list would freeze empty.
        self.fields['network_id'].choices = BLANK_CHOICE_DASH + sn_manager.choices


class InstantMessengerProfile(Profile):
    data_manager = im_manager

    user = models.ForeignKey(User, db_index=True,
                             related_name='instant_messenger_profiles',
                             on_delete=models.CASCADE)
    # Choices live on the form (dynamic data) -- see SocialNetworkProfile.
    network_id = models.CharField(max_length=16, db_index=True)
    username = models.CharField(max_length=64)

    def __str__(self):
        return self.username

class InstantMessengerForm(forms.ModelForm):
    network_id = forms.ChoiceField()

    class Meta:
        model = InstantMessengerProfile
        fields = ('network_id', 'username')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # See SocialNetworkForm: populate choices from the live network data.
        self.fields['network_id'].choices = BLANK_CHOICE_DASH + im_manager.choices


class WebsiteProfile(models.Model):
    user = models.ForeignKey(User, db_index=True,
                             related_name='website_profiles',
                             on_delete=models.CASCADE)
    name = models.CharField(max_length=64)
    url = models.URLField()

    def __str__(self):
        return self.url


class WebsiteForm(forms.ModelForm):

    class Meta:
        model = WebsiteProfile
        fields = ('name', 'url')
