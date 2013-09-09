"""Forms for the user_photos application."""
from django import forms
from django.conf import settings

from user_photos.models import Photo
from user_photos.images import process_file
from user_photos.s3 import S3Bucket


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
        bucket = S3Bucket(settings.USER_PHOTOS_ACCESS_KEY,
                          settings.USER_PHOTOS_SECRET_KEY,
                          settings.USER_PHOTOS_BUCKET)
        url, thumb_url = process_file(self.cleaned_data['image_file'],
                                      self.user,
                                      bucket)
        photo = Photo(user=self.user, url=url, thumb_url=thumb_url)
        photo.save()
        return photo
