"""Builders for real image files used by the image tests.

The rest of the image tests mock PIL wholesale, which is fast but structurally
blind: a Mock hands back any attribute asked of it, so an assertion naming a
constant PIL has removed still passes. These builders exist so a few tests can
run real bytes through the real library instead.

"""
import struct
from io import BytesIO

from PIL import Image


def _gradient(size, mode='RGB'):
    """A small image with enough detail that resampling has work to do."""
    w, h = size
    image = Image.new('RGB', size)
    pixels = image.load()
    for y in range(h):
        for x in range(w):
            pixels[x, y] = ((x * 255) // w, (y * 255) // h, (x * y) % 256)

    if mode == 'RGBA':
        image = image.convert('RGBA')
        pixels = image.load()
        for y in range(h):
            for x in range(w):
                r, g, b, _ = pixels[x, y]
                # A real alpha ramp, so a flattened result is detectable.
                pixels[x, y] = (r, g, b, (x * 255) // w)
    elif mode == 'P':
        image = image.convert('P', palette=Image.ADAPTIVE)

    return image


def jpeg_bytes(size=(400, 300)):
    out = BytesIO()
    _gradient(size).save(out, 'JPEG', quality=92)
    return out.getvalue()


def png_bytes(size=(400, 300)):
    """An RGBA PNG. Alpha is the thing that gets lost if a path writes JPEG."""
    out = BytesIO()
    _gradient(size, 'RGBA').save(out, 'PNG')
    return out.getvalue()


def gif_bytes(size=(400, 300)):
    out = BytesIO()
    _gradient(size, 'P').save(out, 'GIF')
    return out.getvalue()


def oriented_jpeg_bytes(orientation=6, size=(400, 300)):
    """A JPEG carrying an EXIF Orientation tag, for orient_image()."""
    out = BytesIO()
    _gradient(size).save(out, 'JPEG', quality=92,
                         exif=_exif_orientation(orientation))
    return out.getvalue()


def _exif_orientation(value):
    """Minimal little-endian TIFF header holding a single Orientation tag."""
    header = b'II' + struct.pack('<HI', 42, 8)
    entry = struct.pack('<HHIHH', 0x0112, 3, 1, value, 0)
    ifd = struct.pack('<H', 1) + entry + struct.pack('<I', 0)
    return b'Exif\x00\x00' + header + ifd


def opened(data):
    """Open bytes as PIL does for an upload, with .format populated."""
    image = Image.open(BytesIO(data))
    image.load()
    return image
