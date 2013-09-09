"""images.py

This module contains image processing routines for the user_photos application.

"""
import datetime
import logging
from io import BytesIO
import os.path
import uuid

from django.conf import settings
from PIL import Image


logger = logging.getLogger(__name__)


def process_file(f, user, bucket):
    """Perform processing on the given uploaded image file:

    * The image is resized if necessary
    * A thumbnail version is created
    * The image and thumbnail are uploaded to an S3 bucket
    * The image and thumbnail URLs are returned as a tuple

    """
    logger.info('Processing image file for {}: {}'.format(user.username, f.name))

    unique_key = uuid.uuid4().hex
    ext = os.path.splitext(f.name)[1]
    filename = '/tmp/' + unique_key + ext
    with open(filename, 'wb') as fp:
        for chunk in f.chunks():
            fp.write(chunk)

    # Resize image if necessary
    image = Image.open(filename)
    if image.size > settings.USER_PHOTOS_MAX_SIZE:
        logger.debug('Resizing from {} to {}'.format(image.size, settings.USER_PHOTOS_MAX_SIZE))
        image.thumbnail(settings.USER_PHOTOS_MAX_SIZE, Image.ANTIALIAS)
        image.save(filename)

    # Create thumbnail
    logger.debug('Creating thumbnail')
    image = Image.open(filename)
    image.thumbnail(settings.USER_PHOTOS_THUMB_SIZE, Image.ANTIALIAS)
    thumb = BytesIO()
    image.save(thumb, format=image.format)

    # Upload both images to S3
    logging.debug('Uploading image')
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    metadata = {'user': user.username, 'date': now}
    file_key = unique_key + ext
    bucket.upload_from_filename(file_key, filename, metadata)

    logging.debug('Uploading thumbnail')
    thumb_key = '{}t{}'.format(unique_key, ext)
    bucket.upload_from_string(thumb_key, thumb.getvalue())

    os.remove(filename)

    logger.info('Completed processing image file for {}: {}'.format(user.username, f.name))

    url_base = '{}/{}/'.format(settings.USER_PHOTOS_BASE_URL,
                               settings.USER_PHOTOS_BUCKET)

    return (url_base + file_key, url_base + thumb_key)
