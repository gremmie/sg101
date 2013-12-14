"""This module contains a function to upload an image file to a S3Bucket.

The image can be resized and a thumbnail can be generated and uploaded as well.

"""
import logging
from io import BytesIO
import os.path
import tempfile
import uuid

from PIL import Image

from core.functions import temp_open


logger = logging.getLogger(__name__)


def upload(fp, bucket, metadata=None, new_size=None, thumb_size=None):
    """Upload an image file to a given S3Bucket.

    The image can optionally be resized and a thumbnail can be generated and
    uploaded as well.

    Parameters:
        fp - The image file to process. This is expected to be an instance of
             Django's UploadedFile class. The file must have a name attribute and
             we expect the name to have an extension. This is extension is
             used for the uploaded image and thumbnail names.
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

    filename = fp.name
    logger.info('Processing image file: %s', filename)

    # Trying to use PIL (or Pillow) on a Django UploadedFile is often
    # problematic because the file is often an in-memory file if it is under
    # a certain size. This complicates matters and many of the operations we try
    # to perform on it fail if this is the case. To get around these issues,
    # we make a copy of the file on the file system and operate on the copy.
    # First generate a unique name and temporary file path.
    unique_key = uuid.uuid4().hex
    ext = os.path.splitext(fp.name)[1]
    temp_name = os.path.join(tempfile.gettempdir(), unique_key + ext)

    # Write the UploadedFile to a temporary file on disk
    with temp_open(temp_name, 'wb') as temp_file:
        for chunk in fp.chunks():
            temp_file.write(chunk)
        temp_file.close()

        # Resize image if necessary
        if new_size:
            image = Image.open(temp_name)
            if image.size > new_size:
                logger.debug('Resizing from {} to {}'.format(image.size, new_size))
                image.thumbnail(new_size, Image.ANTIALIAS)
                image.save(temp_name)

        # Create thumbnail if necessary
        thumb = None
        if thumb_size:
            logger.debug('Creating thumbnail {}'.format(thumb_size))
            image = Image.open(temp_name)
            image.thumbnail(thumb_size, Image.ANTIALIAS)
            thumb = BytesIO()
            image.save(thumb, format=image.format)

        # Upload images to S3
        file_key = unique_key + ext
        logging.debug('Uploading image')
        image_url = bucket.upload_from_filename(file_key, temp_name, metadata)

    thumb_url = None
    if thumb:
        logging.debug('Uploading thumbnail')
        thumb_key = '{}t{}'.format(unique_key, ext)
        thumb_url = bucket.upload_from_string(thumb_key,
                                              thumb.getvalue(),
                                              metadata)

    logger.info('Completed processing image file: %s', filename)

    return (image_url, thumb_url)
