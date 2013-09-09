"""Forms for the user_photos application."""
from django import forms

from user_photos.models import Photo
from user_photos.images import process_file


class UploadForm(forms.Form):
    image_file = forms.ImageField()

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        super(UploadForm, self).__init__(*args, **kwargs)

    def save(self):
        """Processes the image and creates a new Photo object, which is saved to
        the database. The new Photo instance is returned.

        This function should only be called if is_valid() returns True.

        """
        url, thumb_url = process_file(self.cleaned_data['image_file'], self.user)
        photo = Photo(user=self.user, url=url, thumb_url=thumb_url)
        photo.save()
        return photo
