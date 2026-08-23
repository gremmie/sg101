"""
This file contains the forms used by the bio application.
"""
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from io import BytesIO

from django import forms
from django.conf import settings
from django.core.files.base import ContentFile
from django.urls import reverse
from django.contrib.auth.models import User


from accounts.models import PendingEmailChange
from bio.models import UserProfile
from core.html import image_check
from core.html import ImageCheckError
from core.images.utils import parse_image, downscale_image_square
from core.markup import site_markup


class EditUserForm(forms.ModelForm):
    """Form for editing the fields of the User model.

    email is deliberately declared here rather than listed in Meta.fields. A
    ModelForm writes its Meta fields to the instance, and an address is not the
    member's until they have answered mail sent to it -- so the form cannot be
    allowed to touch User.email at all. The view asks requested_email() and
    starts the confirmation flow instead.

    """
    email = forms.EmailField(label='Email', required=True)

    class Meta:
        model = User
        fields = ('first_name', 'last_name')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Meta fields are populated from the instance; a declared field is not.
        self.fields['email'].initial = self.instance.email

    def clean_email(self):
        email = self.cleaned_data['email'].strip()

        if email.lower() == self.instance.email.lower():
            # Not a change, so there is nothing to check -- and this guard is
            # the whole point of the method. Some accounts share an address
            # with another account, and a uniqueness check that ran
            # unconditionally would lock every one of those members out of
            # saving any profile edit, forever, including edits that never
            # touch this field. It is the constraint
            # accounts.forms.ForgotUsernameForm handles from the recovery
            # side.
            return self.instance.email

        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                'That email address is already in use by another account.')

        if PendingEmailChange.objects.active().filter(
                new_email__iexact=email).exclude(user=self.instance).exists():
            raise forms.ValidationError(
                'Another member has asked to move to that email address and '
                'has not confirmed it yet. Please try again tomorrow.')

        return email

    def requested_email(self):
        """Return the address the member asked for, or None if it is unchanged.

        A case-only edit of the member's own address is not a change: it is the
        same mailbox, and treating it as one would make them confirm an address
        they already hold.

        """
        email = self.cleaned_data['email']
        return None if email.lower() == self.instance.email.lower() else email


class EditUserProfileForm(forms.ModelForm):
    """Form for editing the fields of the UserProfile model."""
    time_zone = forms.CharField(required=False, widget=forms.HiddenInput())
    use_24_time = forms.BooleanField(label='Show times in 24-hour mode', required=False)
    hide_email = forms.BooleanField(
        label="Don't show my email address on my public profile",
        required=False)
    auto_favorite = forms.BooleanField(
        label='Automatically favorite every forum topic I create or reply to',
        required=False)
    auto_subscribe = forms.BooleanField(
        label='Automatically subscribe to every forum topic I create or reply to',
        required=False)

    class Meta:
        model = UserProfile
        fields = ('location', 'country', 'birthday', 'occupation', 'interests',
            'profile_text', 'hide_email', 'signature', 'time_zone',
            'use_24_time', 'auto_favorite', 'auto_subscribe')

    def clean_time_zone(self):
        """Ensure the timezone is valid and will work with ZoneInfo.

        A blank (empty) value is allowed.
        """

        tz = self.cleaned_data['time_zone'].strip()
        if tz:
            try:
                ZoneInfo(tz)
            except (ZoneInfoNotFoundError, ValueError):
                # Both, not just the obvious one: ZoneInfo raises
                # ZoneInfoNotFoundError for a name it does not know, but
                # ValueError for anything path-shaped like '../etc/passwd'.
                # This field is posted by users, so catching only the first
                # would turn a bad value into a 500 instead of a form error.
                raise forms.ValidationError('Invalid timezone')

        return tz

    def _image_check(self, field_name):
        text = self.cleaned_data[field_name]
        if text:
            html = site_markup(text)
            try:
                image_check(html)
            except ImageCheckError as ex:
                raise forms.ValidationError(str(ex))
        return text

    def clean_profile_text(self):
        return self._image_check('profile_text')

    def clean_signature(self):
        return self._image_check('signature')


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
            # Stash the format now, while the image is still the one parse_image()
            # opened. save() downscales through downscale_image_square(), whose
            # crop()/resize() return new images with .format set to None, so by
            # then there is nothing left to read it from.
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
            s = BytesIO()
            self.image.save(s, self.file_type)
            return name, ContentFile(s.getvalue())

        return name, self.cleaned_data['avatar_file']


class SearchUsersForm(forms.Form):
    """
    A form to search for users.
    """
    username = forms.CharField(
                    max_length=30,
                    widget=forms.TextInput(attrs={
                       'class': 'sg101-autocomplete',
                    }))

    def __init__(self, *args, **kwargs):
        super(SearchUsersForm, self).__init__(*args, **kwargs)
        url = reverse('core-ajax_users')
        self.fields['username'].widget.attrs['data-autocomplete-url'] = url

    def clean_username(self):
        username = self.cleaned_data['username'].strip()
        try:
            User.objects.get(username__iexact=username, is_active=True)
        except User.DoesNotExist:
            raise forms.ValidationError("That username does not exist.")
        return username
