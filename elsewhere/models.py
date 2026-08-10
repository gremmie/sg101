from django import forms
from django.db import models
from django.db.models.fields import BLANK_CHOICE_DASH
from django.core.cache import cache
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from django.template.defaultfilters import slugify
from django.urls import reverse
from django.utils import timezone

GOOGLE_PROFILE_URL = 'http://www.google.com/s2/favicons?domain_url=%s'
SN_CACHE_KEY = 'elsewhere_sn_data'
IM_CACHE_KEY = 'elsewhere_im_data'


class Network(models.Model):
    """ Model for storing networks. """

    name = models.CharField(max_length=100)
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
    cache_key = SN_CACHE_KEY
    data = cache.get(cache_key)

    if not data:
        data = {}

        try:
            for network in SocialNetwork.objects.iterator():
                id = slugify(network.name)
                data[id] = {
                    'id': id,
                    'name': network.name,
                    'url': network.url,
                    'identifier': network.identifier,
                    'icon': network.icon
                }
            cache.set(cache_key, data, 60*60*24)
        except:
            # if we haven't yet synced the database, don't worry about this yet
            pass

    return data

def get_instant_messanger_data():
    cache_key = IM_CACHE_KEY
    data = cache.get(cache_key)

    if not data:
        data = {}
        try:
            for network in InstantMessenger.objects.iterator():
                id = slugify(network.name)
                data[id] = {
                    'id': id,
                    'name': network.name,
                    'url': network.url,
                    'icon': network.icon
                }
            cache.set(cache_key, data, 60*60*24)
        except:
            # if we haven't yet synced the database, don't worry about this yet
            pass

    return data

class ProfileManager:
    """ Handle raw data for dicts of profiles."""
    data = {}

    def _get_choices(self):
        """ List of choices for profile select fields. """
        return [(props['id'], props['name']) for props in self.data.values()]
    choices = property(_get_choices)

class SocialNetworkManager(ProfileManager):
    _data = {}
    def _get_data(self):
        if not self._data:
            self._data = get_social_network_data()
        return self._data
    data = property(_get_data)
sn_manager = SocialNetworkManager()

class InstantMessengerManager(ProfileManager):
    _data = {}
    def _get_data(self):
        if not self._data:
            self._data = get_instant_messanger_data()
        return self._data
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
        # Find profile data for this profile id
        return self.data_manager.data[self.network_id]
    data_item = property(_get_data_item)

    def _get_name(self):
        # Profile display name
        return self.data_item['name']
    name = property(_get_name)

    def _get_url(self):
        # Profile URL with username
        return self.data_item['url'] % self.username
    url = property(_get_url)

    def _get_icon_name(self):
        # Icon name
        return self.data_item['icon']
    icon_name = property(_get_icon_name)

    def _get_icon(self):
        # Icon URL or link to Google icon service
        if self.icon_name:
            return reverse('elsewhere_img', args=[self.icon_name])
        return GOOGLE_PROFILE_URL % self.url
    icon = property(_get_icon)

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

    def _get_icon(self):
        # No known icons! Just return the Google service URL.
        return GOOGLE_PROFILE_URL % self.url
    icon = property(_get_icon)


class WebsiteForm(forms.ModelForm):

    class Meta:
        model = WebsiteProfile
        fields = ('name', 'url')
