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
import json
import logging
import os
import re
import signal
import urlparse
import uuid

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from lxml import etree
import lxml.html
import markdown.inlinepatterns
from PIL import Image
import requests

from bio.models import UserProfile
from comments.models import Comment
from forums.models import Post
from core.download import download_file
from core.functions import remove_file
from core.s3 import S3Bucket
from news.models import Story


LOGFILE = os.path.join(settings.PROJECT_PATH, 'logs', 'ssl_images.log')
logger = logging.getLogger(__name__)

IMAGE_LINK_RE = re.compile(markdown.inlinepatterns.IMAGE_LINK_RE,
                           re.DOTALL | re.UNICODE)
IMAGE_REF_RE = re.compile(markdown.inlinepatterns.IMAGE_REFERENCE_RE,
                          re.DOTALL | re.UNICODE)

SG101_HOSTS = set(['www.surfguitar101.com', 'surfguitar101.com'])
WHITELIST_HOSTS = set(settings.USER_IMAGES_SOURCES)
MODEL_CHOICES = ['comments', 'posts', 'news', 'profiles']

PHOTO_MAX_SIZE = (660, 720)
PHOTO_BASE_URL = settings.HOT_LINK_PHOTOS_BASE_URL
PHOTO_BUCKET_NAME = settings.HOT_LINK_PHOTOS_BUCKET

CACHE_FILENAME = 'ssl_images_cache.json'

quit_flag = False
bucket = None
url_cache = {}
bad_hosts = set()
request_timeout = None


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

    requests_log = logging.getLogger("requests.packages.urllib3")
    requests_log.setLevel(logging.INFO)
    requests_log.propagate = True
    requests_log.addHandler(handler)

    dl_log = logging.getLogger("core.download")
    dl_log.setLevel(logging.INFO)
    dl_log.propagate = True
    dl_log.addHandler(handler)


def resize_image(img_path):
    """Resizes the image found at img_path if necessary.

    Returns True if the image was resized or resizing wasn't necessary.
    Returns False if the image could not be read or processed.
    """
    try:
        image = Image.open(img_path)
    except IOError as ex:
        logger.error("Error opening %s: %s", img_path, ex)
        return False

    if image.size > PHOTO_MAX_SIZE:
        logger.info('Resizing from %s to %s', image.size, PHOTO_MAX_SIZE)
        try:
            image.thumbnail(PHOTO_MAX_SIZE, Image.ANTIALIAS)
            image.save(img_path)
        except IOError as ex:
            logger.error("Error resizing image from %s: %s", img_path, ex)
            return False

    return True


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

    if parsed_url.hostname in bad_hosts:
        logger.info("Host known to be bad, skipping: %s", src)
        return None

    # Check the cache
    try:
        new_url = url_cache[src]
    except KeyError:
        # cache miss, try to get the file
        new_url = save_image_to_cloud(parsed_url)
        url_cache[src] = new_url
    else:
        if new_url:
            logger.info("Found URL in cache: %s => %s", src, new_url)
        else:
            logger.info("URL known to be bad, skipping: %s", src)

    return new_url


def save_image_to_cloud(parsed_url):
    """Downloads an image at a given source URL. Uploads it to cloud storage.

    Returns the new URL or None if unsuccessful.
    """
    url = parsed_url.geturl()
    fn = None
    try:
        fn = download_file(url, timeout=request_timeout)
    except requests.ConnectionError as ex:
        logger.error("ConnectionError, ignoring host %s", parsed_url.hostname)
        bad_hosts.add(parsed_url.hostname)
    except requests.RequestException as ex:
        logger.error("%s", ex)
    except Exception as ex:
        logger.exception("%s", ex)

    if fn:
        with remove_file(fn):
            if resize_image(fn):
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
        try:
            r = urlparse.urlparse(src)
        except ValueError:
            return u'{bad image}'

        if r.hostname in SG101_HOSTS:
            new_src = r.path        # convert to relative path
        elif r.scheme == 'http':
            # Try a few things to get this on ssl:
            new_src = convert_to_ssl(r)
        elif r.scheme == 'https':
            if r.hostname in WHITELIST_HOSTS:
                new_src = src   # already in whitelist
            else:
                new_src = convert_to_ssl(r)

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


def process_html(html):
    """Process the html fragment, converting to https where needed."""
    s = html.strip()
    if not s:
        return s

    changed = False
    root = lxml.html.fragment_fromstring(s, create_parent=True)
    for img in root.iter('img'):
        src = img.get('src')
        src = src.strip() if src else ''
        if src:
            try:
                r = urlparse.urlparse(src)
            except ValueError:
                logger.warning("Bad url? Should not happen; skipping...")
                continue

            new_src = None
            if r.hostname in SG101_HOSTS:
                new_src = r.path        # convert to relative path
            elif ((r.scheme == 'http') or
                  (r.scheme == 'https' and r.hostname not in WHITELIST_HOSTS)):
                new_src = convert_to_ssl(r)
                if not new_src:
                    # failed to convert to https; convert to a link
                    tail = img.tail
                    img.clear()
                    img.tag = 'a'
                    img.set('href', src)
                    img.text = 'Image'
                    img.tail = tail
                    changed = True

            if new_src:
                img.set('src', new_src)
                changed = True

    if changed:
        result = lxml.html.tostring(root, encoding='utf-8')
        result = result[5:-6]     # strip off parent div we added
        return result.decode('utf-8')
    return html


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


class Command(BaseCommand):
    help = "Rewrite forum posts and comments to not use http for images"

    def add_arguments(self, parser):
        parser.add_argument('-m', '--model',
                choices=MODEL_CHOICES,
                help="which model to update; must be one of {{{}}}".format(
                                                    ', '.join(MODEL_CHOICES)))
        parser.add_argument('-i', '--i',
                type=int,
                help="optional first slice index; the i in [i:j]")
        parser.add_argument('-j', '--j',
                type=int,
                help="optional second slice index; the j in [i:j]")
        parser.add_argument('-t', '--timeout',
                type=float,
                default=30.0,
                help="optional socket timeout (secs)")

    def handle(self, *args, **options):
        time_started = datetime.datetime.now()
        _setup_logging()
        logger.info("Starting; arguments received: %s", options)

        if options['model'] not in MODEL_CHOICES:
            raise CommandError('Please choose a --model option')

        save_kwargs = {}
        if options['model'] == 'comments':
            qs = Comment.objects.all()
            text_attrs = ['comment']
            model_name = 'Comment'
        elif options['model'] == 'posts':
            qs = Post.objects.all()
            text_attrs = ['body']
            model_name = 'Post'
        elif options['model'] == 'profiles':
            qs = UserProfile.objects.all()
            text_attrs = ['profile_text', 'signature']
            model_name = 'UserProfile'
            save_kwargs = {'content_update': True}
        else:
            qs = Story.objects.all()
            text_attrs = ['short_text', 'long_text']
            model_name = 'Story'

        html_based = options['model'] == 'news'

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
        global request_timeout
        request_timeout = options.get('timeout')
        logger.info("Using socket timeout of %4.2f", request_timeout)

        # Install signal handler for ctrl-c
        signal.signal(signal.SIGINT, signal_handler)

        # Create bucket to upload photos
        global bucket
        bucket = S3Bucket(access_key=settings.USER_PHOTOS_ACCESS_KEY,
                          secret_key=settings.USER_PHOTOS_SECRET_KEY,
                          base_url=PHOTO_BASE_URL,
                          bucket_name=PHOTO_BUCKET_NAME)

        # Load cached info from previous runs
        load_cache()

        if i is None:
            i = 0

        count = 0
        for n, model in enumerate(qs.iterator()):
            if quit_flag:
                logger.warning("SIGINT received, exiting")
                break
            logger.info("Processing %s #%d (pk = %d)", model_name, n + i, model.pk)
            save_flag = False
            for text_attr in text_attrs:
                txt = getattr(model, text_attr)

                if html_based:
                    new_txt = process_html(txt)
                else:
                    new_txt = process_post(txt)
                    warn_if_image_refs(txt, model_name, model.pk)

                if txt != new_txt:
                    logger.info("Content changed on %s #%d (pk = %d)",
                                model_name, n + i, model.pk)
                    logger.debug(u"original: %s", txt)
                    logger.debug(u"changed:  %s", new_txt)
                    setattr(model, text_attr, new_txt)
                    save_flag = True
                elif not html_based and hasattr(model, 'html') and html_check(model.html):
                    # Check for content generated with older smiley code that used
                    # absolute URLs for the smiley images. If True, then just save
                    # the model again to force updated HTML to be created.
                    logger.info("Older Smiley HTML detected, forcing a save")
                    save_flag = True

            if save_flag:
                model.save(**save_kwargs)
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

        save_cache()
        logger.info("ssl_images done")


def load_cache():
    """Load cache from previous runs."""
    logger.info("Loading cached information")
    try:
        with open(CACHE_FILENAME, 'r') as fp:
            d = json.load(fp)
    except IOError as ex:
        logger.error("Cache file (%s) IOError: %s", CACHE_FILENAME, ex)
        return
    except ValueError:
        logger.error("Mangled cache file: %s", CACHE_FILENAME)
        return

    global bad_hosts, url_cache
    try:
        bad_hosts = set(d['bad_hosts'])
        url_cache = d['url_cache']
    except KeyError:
        logger.error("Malformed cache file: %s", CACHE_FILENAME)


def save_cache():
    """Save our cache to a file for future runs."""
    logger.info("Saving cached information")
    d = {'bad_hosts': list(bad_hosts), 'url_cache': url_cache}
    with open(CACHE_FILENAME, 'w') as fp:
        json.dump(d, fp, indent=4)
