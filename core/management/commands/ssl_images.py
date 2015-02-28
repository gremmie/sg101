"""
ssl_images is a custom manage.py command to convert forum post and comment
images to https. It does this by rewriting the markup:
    - Images with src = http://surfguitar101.com/something are rewritten to be
      /something.
    - Non SG101 images that use http: are downloaded, resized, and uploaded to
      an S3 bucket. The src attribute is replaced with the new S3 URL.
"""
import base64
import datetime
import logging
from optparse import make_option
import os
import re
import signal
import socket
import urllib
import urlparse
import uuid

from django.core.management.base import NoArgsCommand, CommandError
from django.conf import settings
from lxml import etree
import markdown.inlinepatterns
from PIL import Image

from comments.models import Comment
from forums.models import Post
from core.s3 import S3Bucket


LOGFILE = os.path.join(settings.PROJECT_PATH, 'logs', 'ssl_images.log')
logger = logging.getLogger(__name__)

IMAGE_LINK_RE = re.compile(markdown.inlinepatterns.IMAGE_LINK_RE,
                           re.DOTALL | re.UNICODE)
IMAGE_REF_RE = re.compile(markdown.inlinepatterns.IMAGE_REFERENCE_RE,
                          re.DOTALL | re.UNICODE)

SG101_HOSTS = set(['www.surfguitar101.com', 'surfguitar101.com'])
MODEL_CHOICES = ['comments', 'posts']

PHOTO_MAX_SIZE = (660, 720)
PHOTO_BASE_URL = 'https://s3.amazonaws.com/'
PHOTO_BUCKET_NAME = 'sg101.forum.photos'

quit_flag = False
opener = None
bucket = None
url_cache = {}


def signal_handler(signum, frame):
    """SIGINT signal handler"""
    global quit_flag
    quit_flag = True


def _setup_logging():
    logger.setLevel(logging.DEBUG)
    logger.propagate = False
    handler = logging.FileHandler(filename=LOGFILE, encoding='utf-8')
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)


class ImageURLopener(urllib.FancyURLopener):
    """Our URL opener. Handles redirects as per FancyURLopener. But all other
    errors and authentication requests will raise an IOError.
    """
    HANDLED_ERRORS = set([302, 301, 303, 307])

    def http_error_default(self, url, fp, errcode, errmsg, headers):
        return urllib.URLopener.http_error_default(self, url, fp, errcode,
                                                   errmsg, headers)

    def http_error(self, url, fp, errcode, errmsg, headers, data=None):
        """Handle http errors.
        We let FancyURLopener handle the redirects, but any other error we want
        to let fail.
        """
        if errcode in self.HANDLED_ERRORS:
            name = 'http_error_%d' % errcode
            method = getattr(self, name)
            if data is None:
                result = method(url, fp, errcode, errmsg, headers)
            else:
                result = method(url, fp, errcode, errmsg, headers, data)
            if result:
                return result
        return self.http_error_default(url, fp, errcode, errmsg, headers)


def download_image(src):
    """Downloads the image file from the given source URL.

    If successful returns the path to the downloaded file. Otherwise None is
    returned.
    """
    logger.info("Retrieving %s", src)
    try:
        fn, hdrs = opener.retrieve(src)
    except IOError as ex:
        args = ex.args
        if len(args) == 4 and args[0] == 'http error':
            logger.error("http error: %d - %s", args[1], args[2])
        else:
            logger.error("%s", ex)
        return None

    # Does it look like an image?
    content_type = hdrs.get('content-type')
    if not content_type:
        logger.error("No content-type header found")
        return None

    file_size = os.stat(fn).st_size
    logger.info("Retrieved: %s bytes; content-type: %s", file_size, content_type)

    parts = content_type.split('/')
    if len(parts) < 2 or parts[0] != 'image':
        logger.error("Unknown content-type: %s", content_type)
        return None

    return fn


def resize_image(img_path):
    """Resizes the image found at img_path if necessary."""
    image = Image.open(img_path)
    if image.size > PHOTO_MAX_SIZE:
        logger.info('Resizing from %s to %s', image.size, PHOTO_MAX_SIZE)
        image.thumbnail(PHOTO_MAX_SIZE, Image.ANTIALIAS)
        image.save(img_path)


def gen_key():
    """Return a random key."""
    return base64.b64encode(uuid.uuid4().bytes, '-_').rstrip('=')


def upload_image(img_path):
    """Upload image file located at img_path to our S3 bucket.

    Returns the URL of the image in the bucket or None if an error occurs.
    """
    logger.info("upload_image starting")
    # Make a unique name for the image in the bucket
    ext = os.path.splitext(img_path)[1]
    file_key = gen_key() + ext
    try:
        return bucket.upload_from_filename(file_key, img_path, public=True)
    except IOError as ex:
        logger.error("Error uploading file: %s", ex)
    return None


def convert_to_ssl(parsed_url):
    """Top-level function for moving an image to SSL."""

    src = parsed_url.geturl()

    # Check the cache first
    try:
        new_url = url_cache[src]
    except KeyError:
        # cache miss, try to get the file
        new_url = save_image_to_cloud(src)
        url_cache[src] = new_url
    else:
        if new_url:
            logger.info("Found URL in cache: %s => %s", src, new_url)
        else:
            logger.info("URL known to be bad, skipping: %s", src)

    return new_url


def save_image_to_cloud(src):
    """Downloads an image at a given source URL. Uploads it to cloud storage.

    Returns the new URL or None if unsuccessful.
    """
    fn = download_image(src)
    if fn:
        resize_image(fn)
        return upload_image(fn)
    return None


def replace_image_markup(match):
    src_parts = match.group(8).split()
    if src_parts:
        src = src_parts[0]
        if src[0] == "<" and src[-1] == ">":
            src = src[1:-1]
    else:
        src = ''

    title = ''
    if len(src_parts) > 1:
        title = " ".join(src_parts[1:])
    alt = match.group(1)

    new_src = None
    if src:
        r = urlparse.urlparse(src)
        if r.hostname in SG101_HOSTS:
            new_src = r.path        # convert to relative path
        elif r.scheme == 'http':
            # Try a few things to get this on ssl:
            new_src = convert_to_ssl(r)
        elif r.scheme == 'https':
            new_src = src       # already https, accept it as-is

    if new_src:
        if title:
            s = u'![{alt}]({src} {title})'.format(alt=alt, src=new_src, title=title)
        else:
            s = u'![{alt}]({src})'.format(alt=alt, src=new_src)
    else:
        # something's messed up, convert to a link using original src
        s = u'[{alt}]({src})'.format(alt=alt, src=src)

    return s


def warn_if_image_refs(text, model_name, pk):
    """Search text for Markdown image reference markup.

    We aren't expecting these, but we will log something if we see any.
    """
    if IMAGE_REF_RE.search(text):
        logger.warning("Image reference found in %s pk = #%d", model_name, pk)


def process_post(text):
    """Process the post object:

    A regex substitution is run on the post's text field. This fixes up image
    links, getting rid of plain old http sources; either converting to https
    or relative style links (if the link is to SG101).

    """
    return IMAGE_LINK_RE.sub(replace_image_markup, text)


def html_check(html):
    """Return True if the given HTML fragment has <img> tags with src attributes
    that use http, and False otherwise.
    """
    if not html:
        return False

    root = etree.HTML(html)
    for img in root.iter('img'):
        src = img.get('src')
        if src and src.lower().startswith('http:'):
            return True
    return False


class Command(NoArgsCommand):
    help = "Rewrite forum posts and comments to not use http for images"
    option_list = NoArgsCommand.option_list + (
            make_option('-m', '--model',
                choices=MODEL_CHOICES,
                help="which model to update; must be one of {{{}}}".format(
                                                    ', '.join(MODEL_CHOICES))),
            make_option('-i', '--i',
                type='int',
                help="optional first slice index; the i in [i:j]"),
            make_option('-j', '--j',
                type='int',
                help="optional second slice index; the j in [i:j]"),
            make_option('-t', '--timeout',
                type='int',
                help="optional socket timeout (secs)"),
            )

    def handle_noargs(self, **options):
        time_started = datetime.datetime.now()
        _setup_logging()
        logger.info("Starting; arguments received: %s", options)

        if options['model'] not in MODEL_CHOICES:
            raise CommandError('Please choose a --model option')

        if options['model'] == 'comments':
            qs = Comment.objects.all()
            text_attr = 'comment'
            model_name = 'Comment'
        else:
            qs = Post.objects.all()
            text_attr = 'body'
            model_name = 'Post'

        i, j = options['i'], options['j']

        if i is not None and i < 0:
            raise CommandError("-i must be >= 0")
        if j is not None and j < 0:
            raise CommandError("-j must be >= 0")
        if j is not None and i is not None and j <= i:
            raise CommandError("-j must be > -i")

        if i is not None and j is not None:
            qs = qs[i:j]
        elif i is not None and j is None:
            qs = qs[i:]
        elif i is None and j is not None:
            qs = qs[:j]

        # Set global socket timeout
        timeout = options.get('timeout', 30)
        logger.info("Setting socket timeout to %d", timeout)
        socket.setdefaulttimeout(timeout)

        # Install signal handler for ctrl-c
        signal.signal(signal.SIGINT, signal_handler)

        # Create URL opener to download photos
        global opener
        opener = ImageURLopener()

        # Create bucket to upload photos
        global bucket
        bucket = S3Bucket(access_key=settings.USER_PHOTOS_ACCESS_KEY,
                          secret_key=settings.USER_PHOTOS_SECRET_KEY,
                          base_url=PHOTO_BASE_URL,
                          bucket_name=PHOTO_BUCKET_NAME)

        if i is None:
            i = 0

        count = 0
        for n, model in enumerate(qs.iterator()):
            if quit_flag:
                logger.warning("SIGINT received, exiting")
                break
            logger.info("Processing %s #%d (pk = %d)", model_name, n + i, model.pk)
            txt = getattr(model, text_attr)
            warn_if_image_refs(txt, model_name, model.pk)
            new_txt = process_post(txt)
            if txt != new_txt:
                logger.info("Content changed on %s #%d (pk = %d)",
                            model_name, n + i, model.pk)
                logger.debug("original: %s", txt)
                logger.debug("changed:  %s", new_txt)
                setattr(model, text_attr, new_txt)
                model.save()
            elif html_check(model.html):
                # Check for content generated with older smiley code that used
                # absolute URLs for the smiley images. If True, then just save
                # the model again to force updated HTML to be created.
                logger.info("Older Smiley HTML detected, forcing a save")
                model.save()
            count += 1

        time_finished = datetime.datetime.now()
        elapsed = time_finished - time_started
        logger.info("ssl_images exiting; number of objects: %d; elapsed: %s",
                    count, elapsed)

        http_images = len(url_cache)
        https_images = sum(1 for v in url_cache.itervalues() if v)
        bad_images = http_images - https_images
        if http_images > 0:
            pct_saved = float(https_images) / http_images * 100.0
        else:
            pct_saved = 0.0

        logger.info("Summary: http: %d; https: %d; lost: %d; saved: %3.1f %%",
                    http_images, https_images, bad_images, pct_saved)
