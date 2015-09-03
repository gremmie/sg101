"""Forms for the user_photos application."""
import datetime
import hashlib
import os.path

from django import forms
from django.conf import settings

from core.s3 import S3Bucket
from core.image_uploader import upload
from core.functions import TemporaryFile
from core.services import get_redis_connection
from user_photos.models import Photo


def rate_limit(key, limit, seconds):
    """Use Redis to do a rate limit check. Returns True if the limit is violated
    and False otherwise.

    key - the key to check in Redis
    limit - the rate limit maximum value
    seconds - the rate limit period in seconds

    """
    conn = get_redis_connection()
    val = conn.incr(key)
    if val == 1:
        conn.expire(key, seconds)
    return val > limit


class UploadForm(forms.Form):
    image_file = forms.ImageField()

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        super(UploadForm, self).__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super(UploadForm, self).clean()

        # rate limit uploads
        key = 'user_photos:counts:' + self.user.username
        limit = settings.USER_PHOTOS_RATE_LIMIT
        if rate_limit(key, *limit):
            raise forms.ValidationError("You've exceeded your upload quota. "
                    "Please try again later.")

        return cleaned_data

    def save(self):
        """Processes the image and creates a new Photo object, which is saved to
        the database. The new Photo instance is returned.

        Note that we do de-duplication. A signature is computed for the photo.
        If the user has already uploaded a file with the same signature, that
        photo object is returned instead.

        This function should only be called if is_valid() returns True.

        """
        # Check for duplicate uploads from this user
        signature = self._signature()
        try:
            return Photo.objects.get(user=self.user, signature=signature)
        except Photo.DoesNotExist:
            pass

        # This must not be a duplicate, proceed with upload to S3
        bucket = S3Bucket(access_key=settings.USER_PHOTOS_ACCESS_KEY,
                          secret_key=settings.USER_PHOTOS_SECRET_KEY,
                          base_url=settings.USER_PHOTOS_BASE_URL,
                          bucket_name=settings.USER_PHOTOS_BUCKET)

        # Trying to use PIL (or Pillow) on a Django UploadedFile is often
        # problematic because the file is often an in-memory file if it is under
        # a certain size. This complicates matters and many of the operations we try
        # to perform on it fail if this is the case. To get around these issues,
        # we make a copy of the file on the file system and operate on the copy.

        fp = self.cleaned_data['image_file']
        ext = os.path.splitext(fp.name)[1]

        # Write the UploadedFile to a temporary file on disk
        with TemporaryFile(suffix=ext) as t:
            for chunk in fp.chunks():
                t.file.write(chunk)
            t.file.close()

            now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            metadata = {'user': self.user.username, 'date': now}

            url, thumb_url = upload(filename=t.filename,
                                    bucket=bucket,
                                    metadata=metadata,
                                    new_size=settings.USER_PHOTOS_MAX_SIZE,
                                    thumb_size=settings.USER_PHOTOS_THUMB_SIZE)

        photo = Photo(user=self.user, url=url, thumb_url=thumb_url,
                signature=signature)
        photo.save()
        return photo

    def _signature(self):
        """Calculates and returns a signature for the image file as a hex digest
        string.

        This function should only be called if is_valid() is True.

        """
        fp = self.cleaned_data['image_file']
        md5 = hashlib.md5()
        for chunk in fp.chunks():
            md5.update(chunk)
        return md5.hexdigest()
