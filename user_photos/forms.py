"""Forms for the user_photos application."""
import datetime

from django import forms
from django.conf import settings

from core.s3 import S3Bucket
from core.image_uploader import upload
from user_photos.models import Photo


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
        bucket = S3Bucket(access_key=settings.USER_PHOTOS_ACCESS_KEY,
                          secret_key=settings.USER_PHOTOS_SECRET_KEY,
                          base_url=settings.USER_PHOTOS_BASE_URL,
                          bucket_name=settings.USER_PHOTOS_BUCKET)

        now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        metadata = {'user': self.user.username, 'date': now}

        url, thumb_url = upload(fp=self.cleaned_data['image_file'],
                                bucket=bucket,
                                metadata=metadata,
                                new_size=settings.USER_PHOTOS_MAX_SIZE,
                                thumb_size=settings.USER_PHOTOS_THUMB_SIZE)

        photo = Photo(user=self.user, url=url, thumb_url=thumb_url)
        photo.save()
        return photo
