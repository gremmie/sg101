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

from django.core.management.base import NoArgsCommand, CommandError
from django.conf import settings
import markdown.inlinepatterns

from comments.models import Comment
from forums.models import Post


LOGFILE = os.path.join(settings.PROJECT_PATH, 'logs', 'ssl_images.log')
logger = logging.getLogger(__name__)

IMAGE_LINK_RE = re.compile(markdown.inlinepatterns.IMAGE_LINK_RE)
IMAGE_REF_RE = re.compile(markdown.inlinepatterns.IMAGE_REFERENCE_RE)

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


class CommentFacade(object):
    """Wrapper class to provide uniform access to Comments."""
    def __init__(self, comment):
        self.comment = comment

    @property
    def text(self):
        return self.comment.comment

    @text.setter
    def text(self, value):
        self.comment.comment = value


class PostFacade(object):
    """Wrapper class to provide uniform access to Forum posts."""
    def __init__(self, post):
        self.post = post

    @property
    def text(self):
        return self.post.body

    @text.setter
    def text(self, value):
        self.post.body = value


def process_post(post):
    """Process the post object:

    A regex substitution is run on the post's text field. This fixes up image
    links, getting rid of plain old http sources; either converting to https
    or relative style links (if the link is to SG101).

    We also do a search for Markdown image reference markup. We aren't expecting
    these, but we will log something if we see any.

    """


class Command(NoArgsCommand):
    help = "Rewrite forum posts and comments to not use http for images"
    option_list = NoArgsCommand.option_list + (
            make_option('--forums',
                action='store_true',
                default=False,
                help="process forum posts"),
            make_option('--comments',
                action='store_true',
                default=False,
                help="process comments"),
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

        do_comments = options['comments']
        do_forums = options['forums']
        if do_comments and do_forums:
            raise CommandError("Please specify --forums or --comments, not both")
        elif not do_comments and not do_forums:
            raise CommandError("Please specify --forums or --comments")

        if do_comments:
            qs = Comment.objects.all()
            facade = CommentFacade
        else:
            qs = Post.objects.all()
            facade = PostFacade

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
            obj = facade(model)
            process_post(obj)
            s.append(obj.text)

        import pprint
        pprint.pprint(s)
