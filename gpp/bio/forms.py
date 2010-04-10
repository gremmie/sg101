"""
This file contains the forms used by the bio application.
"""
from PIL import ImageFile
from PIL import Image

try:
    from cStringIO import StringIO
except:
    from StringIO import StringIO

from django import forms
from django.conf import settings
from django.core.files.base import ContentFile
from django.contrib.auth.models import User

from bio.models import UserProfile
from core.widgets import AutoCompleteUserInput


class EditUserForm(forms.ModelForm):
    """Form for editing the fields of the User model."""
    email = forms.EmailField(label='Email', required=True)
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email')


class EditUserProfileForm(forms.ModelForm):
    """Form for editing the fields of the UserProfile model."""
    location = forms.CharField(required=False, widget=forms.TextInput(attrs={'size' : 64 }))
    occupation = forms.CharField(required=False, widget=forms.TextInput(attrs={'size' : 64 }))
    interests = forms.CharField(required=False, widget=forms.TextInput(attrs={'size' : 64 }))
    time_zone = forms.CharField(required=False, widget=forms.HiddenInput())
    use_24_time = forms.BooleanField(label='Show times in 24-hour mode', required=False)
    profile_text = forms.CharField(required=False, 
            widget=forms.Textarea(attrs={'class': 'markItUp'}))
    signature = forms.CharField(required=False, 
            widget=forms.Textarea(attrs={'class': 'markItUp'}))

    class Meta:
        model = UserProfile
        exclude = ('user', 'avatar', 'profile_html', 'signature_html', 'forum_post_count')

    class Media:
        css = {
            'all': settings.GPP_THIRD_PARTY_CSS['markitup'] + \
                settings.GPP_THIRD_PARTY_CSS['jquery-ui']
        }
        js = settings.GPP_THIRD_PARTY_JS['markitup'] + \
            settings.GPP_THIRD_PARTY_JS['jquery-ui'] + \
            ('js/bio.js', 'js/timezone.js')


def get_image(file):
    """
    Returns a PIL Image from the supplied file.
    Throws ValidationError if the file does not parse as an image file.
    """
    parser = ImageFile.Parser()
    for chunk in file.chunks():
        parser.feed(chunk)
    try:
        image = parser.close()
        return image
    except IOError:
        pass
    raise forms.ValidationError("Upload a valid image. " +
            "The file you uploaded was either not an image or a corrupted image.")


def scale_image(image, size):
    """Scales an image file if necessary."""

    # don't upscale
    if (size, size) >= image.size:
        return image

    (w, h) = image.size
    if w > h:
        diff = (w - h) / 2
        image = image.crop((diff, 0, w - diff, h))
    elif h > w:
        diff = (h - w) / 2
        image = image.crop((0, diff, w, h - diff))
    image = image.resize((size, size), Image.ANTIALIAS)
    return image


class UploadAvatarForm(forms.Form):
    """Form used to change a user's avatar"""
    avatar_file = forms.ImageField(required=False)
    image = None

    def clean_avatar_file(self):
        file = self.cleaned_data['avatar_file']
        if file is not None:
            if file.size > settings.MAX_AVATAR_SIZE_BYTES:
                raise forms.ValidationError("Please upload a file smaller than %s bytes." % \
                        settings.MAX_AVATAR_SIZE)
            self.image = get_image(file)
            self.format = self.image.format
        return file

    def get_file(self):
        if self.image is not None:
            self.image = scale_image(self.image, settings.MAX_AVATAR_SIZE_PIXELS)
            s = StringIO()
            self.image.save(s, self.format)
            return ContentFile(s.getvalue())
        return None

    def get_filename(self):
        return self.cleaned_data['avatar_file'].name


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
      username = self.cleaned_data['username']
      try:
         User.objects.get(username=username, is_active=True)
      except User.DoesNotExist:
         raise forms.ValidationError("That username does not exist.")
      return username
