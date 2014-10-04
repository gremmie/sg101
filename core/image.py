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


# Various image transformation functions:
def flip_horizontal(im):
    return im.transpose(Image.FLIP_LEFT_RIGHT)

def flip_vertical(im):
    return im.transpose(Image.FLIP_TOP_BOTTOM)

def rotate_180(im):
    return im.transpose(Image.ROTATE_180)

def rotate_90(im):
    return im.transpose(Image.ROTATE_90)

def rotate_270(im):
    return im.transpose(Image.ROTATE_270)

def transpose(im):
    return rotate_90(flip_horizontal(im))

def transverse(im):
    return rotate_90(flip_vertical(im))

# From http://www.sno.phy.queensu.ca/~phil/exiftool/TagNames/EXIF.html
# EXIF Orientation tag values:
# 1 = Horizontal (normal)
# 2 = Mirror horizontal
# 3 = Rotate 180
# 4 = Mirror vertical
# 5 = Mirror horizontal and rotate 270 CW
# 6 = Rotate 90 CW
# 7 = Mirror horizontal and rotate 90 CW
# 8 = Rotate 270 CW

ORIENT_FUNCS = {
    2: flip_horizontal,
    3: rotate_180,
    4: flip_vertical,
    5: transpose,
    6: rotate_270,
    7: transverse,
    8: rotate_90,
}

ORIENT_TAG = 0x112


def orient_image(im):
    """Transforms the given image according to embedded EXIF data.

    The image instance, im, should be a PIL Image.
    If there is EXIF information for the image, and the orientation tag
    indicates that the image should be transformed, perform the transformation.

    Returns a tuple of the form (flag, image) where flag is True if the image
    was oriented and False otherwise. image is either a new transformed image or
    the original image instance.

    """
    if hasattr(im, '_getexif'):
        exif = im._getexif()
        if exif and ORIENT_TAG in exif:
            orientation = exif[ORIENT_TAG]
            func = ORIENT_FUNCS.get(orientation)
            if func:
                return (True, func(im))

    return (False, im)
