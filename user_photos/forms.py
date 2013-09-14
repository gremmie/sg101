"""Forms for the user_photos application."""
import datetime

from django import forms
from django.conf import settings

from core.s3 import S3Bucket
from core.image_uploader import upload
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
