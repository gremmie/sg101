"""
This file contains common utility functions for manipulating images for
the rest of the applications in the project.
"""
from PIL import ImageFile
from PIL import Image


def parse_image(file):
    """
    Returns a PIL Image from the supplied Django file object.
    Throws IOError if the file does not parse as an image file or some other
    I/O error occurred.

    """
    parser = ImageFile.Parser()
    for chunk in file.chunks():
        parser.feed(chunk)
    image = parser.close()
    return image


def downscale_image_square(image, size):
    """
    Scale an image to the square dimensions given by size (in pixels).
    The new image is returned.
    If the image is already smaller than (size, size) then no scaling
    is performed and the image is returned unchanged.

    """
    # don't upscale
    if (size, size) >= image.size:
        return image

    (w, h) = image.size
    if w > h:
        diff = (w - h) / 2
        image = image.crop((diff, 0, w - diff, h))
    elif h > w:
        diff = (h - w) / 2
        image = image.crop((0, diff, w, h - diff))
    image = image.resize((size, size), Image.ANTIALIAS)
    return image
