"""This module contains a function to upload an image file to a S3Bucket.

The image can be resized and a thumbnail can be generated and uploaded as well.

"""
from base64 import b64encode
import logging
from io import BytesIO
import os.path
import uuid

from PIL import Image

from core.image import orient_image


logger = logging.getLogger(__name__)


def make_key():
    """Generate a random key suitable for a filename"""
    return b64encode(uuid.uuid4().bytes, '-_').rstrip('=')


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
            image.thumbnail(new_size, Image.ANTIALIAS)
            image.save(filename)

    # Create thumbnail if necessary
    thumb = None
    if thumb_size:
        logger.debug('Creating thumbnail {}'.format(thumb_size))
        image = Image.open(filename)
        image.thumbnail(thumb_size, Image.ANTIALIAS)
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
