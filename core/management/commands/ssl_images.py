"""
ssl_images is a custom manage.py command to convert forum post and comment
images to https. It does this by rewriting the markup:
    - Images with src = http://surfguitar101.com/something are rewritten to be
      /something.
    - Non SG101 images that use http: are downloaded, resized, and uploaded to
      an S3 bucket. The src attribute is replaced with the new S3 URL.
"""
import logging
from optparse import make_option
import os.path
import re
import signal
import urlparse

from django.core.management.base import NoArgsCommand, CommandError
from django.conf import settings
import markdown.inlinepatterns

from comments.models import Comment
from forums.models import Post


LOGFILE = os.path.join(settings.PROJECT_PATH, 'logs', 'ssl_images.log')
logger = logging.getLogger(__name__)

IMAGE_LINK_RE = re.compile(markdown.inlinepatterns.IMAGE_LINK_RE, re.UNICODE)
IMAGE_REF_RE = re.compile(markdown.inlinepatterns.IMAGE_REFERENCE_RE, re.UNICODE)

SG101_HOSTS = set(['www.surfguitar101.com', 'surfguitar101.com'])
MODEL_CHOICES = ['comments', 'posts']

quit_flag = False


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


def save_image_to_cloud(src):
    # TODO
    return src


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

    new_src = ''
    if src:
        r = urlparse.urlparse(src)
        if r.scheme == 'http':
            if r.hostname in SG101_HOSTS:
                new_src = r.path    # convert to relative path
            else:
                new_src = save_image_to_cloud(src)
        elif r.scheme == 'https':
            new_src = src       # already https, accept it as-is

    if new_src:
        if title:
            s = u'![{alt}]({src} "{title}")'.format(alt=alt, src=new_src, title=title)
        else:
            s = u'![{alt}]({src})'.format(alt=alt, src=new_src)
    else:
        # something's messed up, convert to a link using original src
        s = u'[{alt}]({src})'.format(alt=alt, src=src)

    return s


def process_post(text):
    """Process the post object:

    A regex substitution is run on the post's text field. This fixes up image
    links, getting rid of plain old http sources; either converting to https
    or relative style links (if the link is to SG101).

    We also do a search for Markdown image reference markup. We aren't expecting
    these, but we will log something if we see any.

    """
    return IMAGE_LINK_RE.sub(replace_image_markup, text)


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
            )

    def handle_noargs(self, **options):
        _setup_logging()
        logger.info("Starting; arguments received: %s", options)

        if options['model'] not in MODEL_CHOICES:
            raise CommandError('Please choose a --model option')

        if options['model'] == 'comments':
            qs = Comment.objects.all()
            text_attr = 'comment'
        else:
            qs = Post.objects.all()
            text_attr = 'body'

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

        # Install signal handler for ctrl-c
        signal.signal(signal.SIGINT, signal_handler)

        s = []
        for model in qs.iterator():
            if quit_flag:
                logger.warning("SIGINT received, exiting")
            txt = getattr(model, text_attr)
            new_txt = process_post(txt)
            s.append(new_txt)

        import pprint
        pprint.pprint(s)
