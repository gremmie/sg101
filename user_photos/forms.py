"""Forms for the user_photos application."""
import hashlib
import os.path
from urllib.parse import urlsplit

from PIL import UnidentifiedImageError
from django import forms
from django.conf import settings

from core.download import DownloadError, NotAccepted, TooLarge, download_file
from core.functions import remove_file, TemporaryFile
from core.images.upload import process_upload
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


def rate_limit_user(user):
    """Shared function to rate limit user uploads."""
    key = 'user_photos:counts:' + user.username
    limit = settings.USER_PHOTOS_RATE_LIMIT
    if rate_limit(key, *limit):
        raise forms.ValidationError("You've exceeded your upload quota. "
                "Please try again later.")


class UploadForm(forms.Form):
    image_file = forms.ImageField()

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        super(UploadForm, self).__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super(UploadForm, self).clean()
        rate_limit_user(self.user)
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

            url, thumb_url = process_upload(self.user, t.filename)

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


class HotLinkError(Exception):
    """A hot-link that cannot work; the message is for the member."""


# A slow or huge download holds one of the web workers for as long as it runs.
HOTLINK_TIMEOUT = 10                     # seconds
HOTLINK_MAX_BYTES = 10 * 1024 * 1024     # far above any photo; it is resized

YOUTUBE_HOSTS = {'youtube.com', 'www.youtube.com', 'm.youtube.com',
                 'music.youtube.com', 'youtu.be'}

YOUTUBE_MESSAGE = (
    "YouTube videos can't be added as images. In a forum post, add the video "
    "under Video Attachments below the post box. Elsewhere, paste the "
    "video's link into your text.")
WEB_PAGE_MESSAGE = (
    "That address isn't an image; it's probably a web page. Open the page, "
    "right-click the picture, choose Copy Image Address, and paste that here.")
FETCH_FAILED_MESSAGE = (
    "We couldn't download an image from that address. Check that it opens "
    "in your browser, then try again.")
TOO_LARGE_MESSAGE = "That image is larger than 10 MB, which is our limit."
UNREADABLE_MESSAGE = (
    "That file isn't an image we can read. Try a JPEG, PNG or GIF.")


class HotLinkImageForm(forms.Form):
    """Form for hot-linking images. If the supplied URL's host is on
    a white-list, return it as-is. Otherwise attempt to download the image at
    the given URL and upload it into our S3 storage. The URL to the new location
    is returned.
    """
    url = forms.URLField()

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        super(HotLinkImageForm, self).__init__(*args, **kwargs)

    def clean_url(self):
        the_url = self.cleaned_data['url']
        self.url_parts = urlsplit(the_url)
        if self.url_parts.scheme not in ['http', 'https']:
            raise forms.ValidationError("Invalid URL scheme")
        # The commonest mistake by far, and one that needs no fetch to spot.
        if self.url_parts.hostname in YOUTUBE_HOSTS:
            raise forms.ValidationError(YOUTUBE_MESSAGE)
        return the_url

    def clean(self):
        cleaned_data = super(HotLinkImageForm, self).clean()
        rate_limit_user(self.user)
        return cleaned_data

    def save(self):
        url = self.url_parts.geturl()
        if (self.url_parts.scheme == 'https' and
                self.url_parts.hostname in settings.USER_IMAGES_SOURCES):
            return url

        try:
            path = download_file(url, timeout=HOTLINK_TIMEOUT,
                                 max_bytes=HOTLINK_MAX_BYTES, accept='image/')
        except NotAccepted:
            raise HotLinkError(WEB_PAGE_MESSAGE)
        except TooLarge:
            raise HotLinkError(TOO_LARGE_MESSAGE)
        except DownloadError:
            raise HotLinkError(FETCH_FAILED_MESSAGE)

        with remove_file(path):
            try:
                url, _ = process_upload(self.user, path)
            except UnidentifiedImageError:
                raise HotLinkError(UNREADABLE_MESSAGE)

        return url
