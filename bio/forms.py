"""
This file contains the forms used by the bio application.
"""
try:
    from cStringIO import StringIO
except:
    from StringIO import StringIO

from django import forms
from django.conf import settings
from django.core.files.base import ContentFile
from django.contrib.auth.models import User

import pytz

from bio.models import UserProfile
from core.widgets import AutoCompleteUserInput
from core.images.utils import parse_image, downscale_image_square


class EditUserForm(forms.ModelForm):
    """Form for editing the fields of the User model."""
    email = forms.EmailField(label='Email', required=True)
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email')


class EditUserProfileForm(forms.ModelForm):
    """Form for editing the fields of the UserProfile model."""
    location = forms.CharField(required=False, widget=forms.TextInput(attrs={'size': 64 }))
    occupation = forms.CharField(required=False, widget=forms.TextInput(attrs={'size': 64 }))
    interests = forms.CharField(required=False, widget=forms.TextInput(attrs={'size': 64 }))
    time_zone = forms.CharField(required=False, widget=forms.HiddenInput())
    use_24_time = forms.BooleanField(label='Show times in 24-hour mode', required=False)
    profile_text = forms.CharField(required=False,
        widget=forms.Textarea(attrs={'class': 'markItUp'}))
    signature = forms.CharField(required=False,
        widget=forms.Textarea(attrs={'class': 'markItUp'}))
    auto_favorite = forms.BooleanField(
        label='Automatically favorite every forum topic I create or reply to', required=False)
    auto_subscribe = forms.BooleanField(
        label='Automatically subscribe to every forum topic I create or reply to', required=False)

    class Meta:
        model = UserProfile
        fields = ('location', 'country', 'birthday', 'occupation', 'interests',
            'profile_text', 'hide_email', 'signature', 'time_zone',
            'use_24_time', 'auto_favorite', 'auto_subscribe')

    class Media:
        css = {
            'all': (settings.GPP_THIRD_PARTY_CSS['markitup'] +
                settings.GPP_THIRD_PARTY_CSS['jquery-ui'])
        }
        js = (settings.GPP_THIRD_PARTY_JS['markitup'] +
            settings.GPP_THIRD_PARTY_JS['jquery-ui'] +
            ['js/bio.js', 'js/timezone.js'])

    def clean_time_zone(self):
        """Ensure the timezone is valid and will work with pytz.
        
        A blank (empty) value is allowed.
        """

        tz = self.cleaned_data['time_zone'].strip()
        if tz:
            try:
                pytz.timezone(tz)
            except pytz.UnknownTimeZoneError:
                raise forms.ValidationError('Invalid timezone')

        return tz


class UploadAvatarForm(forms.Form):
    """Form used to change a user's avatar"""
    avatar_file = forms.ImageField(required=False)
    image = None

    def clean_avatar_file(self):
        f = self.cleaned_data['avatar_file']
        if f is not None:
            if f.size > settings.MAX_AVATAR_SIZE_BYTES:
                raise forms.ValidationError("Please upload a file smaller than "
                    "%s bytes." % settings.MAX_AVATAR_SIZE_BYTES)
            try:
                self.image = parse_image(f)
            except IOError:
                raise forms.ValidationError("Please upload a valid image. "
                    "The file you uploaded was either not an image or a "
                    "corrupted image.")
            self.file_type = self.image.format
        return f

    def save(self):
        """
        Perform any down-scaling needed on the new file, then return a tuple of
        (filename, file object). Note that the file object returned may not
        have a name; use the returned filename instead.

        """
        if not self.cleaned_data['avatar_file']:
            return None, None

        name = self.cleaned_data['avatar_file'].name
        dim = settings.MAX_AVATAR_SIZE_PIXELS
        max_size = (dim, dim)
        if self.image and self.image.size > max_size:
            self.image = downscale_image_square(self.image, dim)

            # We need to return a Django File now. To get that from here,
            # write the image data info a StringIO and then construct a
            # Django ContentFile from that. The ContentFile has no name,
            # that is why we return one ourselves explicitly.
            s = StringIO()
            self.image.save(s, self.file_type)
            return name, ContentFile(s.getvalue())

        return name, self.cleaned_data['avatar_file']


class SearchUsersForm(forms.Form):
    """
    A form to search for users.
    """
    username = forms.CharField(max_length=30, widget=AutoCompleteUserInput())

    class Media:
        css = {
          'all': settings.GPP_THIRD_PARTY_CSS['jquery-ui']
        }
        js = settings.GPP_THIRD_PARTY_JS['jquery-ui']

    def clean_username(self):
      username = self.cleaned_data['username'].strip()
      try:
         User.objects.get(username=username, is_active=True)
      except User.DoesNotExist:
         raise forms.ValidationError("That username does not exist.")
      return username
