"""This module contains a function to upload an image file to a S3Bucket.

The image can be resized and a thumbnail can be generated and uploaded as well.

"""
from base64 import b64encode
import logging
from io import BytesIO
import os
import os.path
import shutil
import uuid

from django.conf import settings
from django.contrib.sites.models import Site
from django.utils import timezone
from PIL import Image

from .utils import orient_image
from core.s3 import S3Bucket


logger = logging.getLogger(__name__)


def process_upload(user, filename):
    if settings.USER_PHOTOS_LOCAL_UPLOAD:
        url, thumb_url = _process_local_upload(
                filename,
                new_size=settings.USER_PHOTOS_MAX_SIZE,
                thumb_size=settings.USER_PHOTOS_THUMB_SIZE)
    else:
        # localtime(), so the stamp stays in TIME_ZONE as it always has -- this
        # string is written into the object's S3 metadata and carries no zone.
        now = timezone.localtime().strftime('%Y-%m-%d %H:%M:%S')
        metadata = {'user': user.username, 'date': now}

        bucket = S3Bucket(access_key=settings.USER_PHOTOS_ACCESS_KEY,
                          secret_key=settings.USER_PHOTOS_SECRET_KEY,
                          base_url=settings.USER_PHOTOS_BASE_URL,
                          bucket_name=settings.USER_PHOTOS_BUCKET)

        url, thumb_url = upload(filename,
                                bucket=bucket,
                                metadata=metadata,
                                new_size=settings.USER_PHOTOS_MAX_SIZE,
                                thumb_size=settings.USER_PHOTOS_THUMB_SIZE)
    return (url, thumb_url)


def make_key():
    """Generate a random key suitable for a filename"""
    return b64encode(uuid.uuid4().bytes, b'-_').rstrip(b'=').decode('ascii')


def upload(filename, bucket, metadata=None, new_size=None, thumb_size=None):
    """Upload an image file to a given S3Bucket.

    The image can optionally be resized and a thumbnail can be generated and
    uploaded as well.

    Parameters:
        filename - The path to the file to process. The filename should have an
                   extension, and this is used for the uploaded image & thumbnail
                   names.
        bucket - A core.s3.S3Bucket instance to upload to.
        metadata - If not None, must be a dictionary of metadata to apply to the
                   uploaded file and thumbnail.
        new_size - If not None, the image will be resized to the dimensions
                   specified by new_size, which must be a (width, height) tuple.
        thumb_size - If not None, a thumbnail image will be created with the
                     dimensions specified by thumb_size, which must be a (width,
                     height) tuple. The thumbnail will use the same metadata, if
                     present, as the image. The thumbnail filename will be the
                     same basename as the image with a 't' appended. The
                     extension will be the same as the original image.

    A tuple is returned: (image_url, thumb_url) where thumb_url will be None if
    a thumbnail was not requested.
    """

    logger.info('Processing image file: %s', filename)

    unique_key = make_key()
    ext = os.path.splitext(filename)[1]

    # Re-orient if necessary
    image = Image.open(filename)
    changed, image = orient_image(image)
    if changed:
        image.save(filename)

    # Resize image if necessary
    if new_size:
        image = Image.open(filename)
        if image.size > new_size:
            logger.debug('Resizing from {} to {}'.format(image.size, new_size))
            image.thumbnail(new_size, Image.Resampling.LANCZOS)
            image.save(filename)

    # Create thumbnail if necessary
    thumb = None
    if thumb_size:
        logger.debug('Creating thumbnail {}'.format(thumb_size))
        image = Image.open(filename)
        image.thumbnail(thumb_size, Image.Resampling.LANCZOS)
        thumb = BytesIO()
        image.save(thumb, format=image.format)

    # Upload images to S3
    file_key = unique_key + ext
    logging.debug('Uploading image')
    image_url = bucket.upload_from_filename(file_key, filename, metadata)

    thumb_url = None
    if thumb:
        logging.debug('Uploading thumbnail')
        thumb_key = '{}t{}'.format(unique_key, ext)
        thumb_url = bucket.upload_from_string(thumb_key,
                                              thumb.getvalue(),
                                              metadata)

    logger.info('Completed processing image file: %s', filename)

    return (image_url, thumb_url)


def _process_local_upload(filename, new_size=None, thumb_size=None):
    # Re-orient if necessary
    image = Image.open(filename)
    changed, image = orient_image(image)
    if changed:
        image.save(filename)

    # Resize image if necessary
    if new_size:
        image = Image.open(filename)
        if image.size > new_size:
            logger.debug('Resizing from {} to {}'.format(image.size, new_size))
            image.thumbnail(new_size, Image.Resampling.LANCZOS)
            image.save(filename)

    # Create thumbnail if necessary
    thumb = None
    if thumb_size:
        logger.debug('Creating thumbnail {}'.format(thumb_size))
        image = Image.open(filename)
        image.thumbnail(thumb_size, Image.Resampling.LANCZOS)
        thumb = BytesIO()
        image.save(thumb, format=image.format)

    # Copy file and thumbnail to our user upload files directory.
    upload_dir = os.path.join(settings.MEDIA_ROOT,
                              settings.USER_PHOTOS_LOCAL_UPLOAD_DIR)
    unique_name = uuid.uuid4().hex
    ext = os.path.splitext(filename)[1]
    image_name = '%s%s' % (unique_name, ext)
    thumb_name = '%st%s' % (unique_name, ext)
    image_path = os.path.join(upload_dir, image_name)
    thumb_path = os.path.join(upload_dir, thumb_name)
    perms = 0o644

    shutil.copy(filename, image_path)
    os.chmod(image_path, perms)

    if thumb:
        thumb.seek(0)
        with open(thumb_path, 'wb') as out:
            out.write(thumb.getvalue())
        os.chmod(thumb_path, perms)

    # Generate URLs for the image and thumb.
    image_url = _user_photo_url(image_name)
    thumb_url = _user_photo_url(thumb_name)

    return (image_url, thumb_url)


def _user_photo_url(filename):
    url_pattern = '%s://%s%s%s/%s'
    site = Site.objects.get_current()

    return url_pattern % (
            settings.SITE_SCHEME,
            site.domain,
            settings.MEDIA_URL,
            settings.USER_PHOTOS_LOCAL_UPLOAD_DIR,
            filename)
