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

from django.core.management.base import NoArgsCommand, CommandError
from django.conf import settings

LOGFILE = os.path.join(settings.PROJECT_PATH, 'logs', 'ssl_images.log')
logger = logging.getLogger(__name__)


def _setup_logging():
    logger.setLevel(logging.DEBUG)
    logger.propagate = False
    handler = logging.FileHandler(filename=LOGFILE, encoding='utf-8')
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)


class Command(NoArgsCommand):
    help = "Rewrite forum posts and comments to not use http for images"
    option_list = NoArgsCommand.option_list + (
            make_option('--forums',
                action='store_true',
                default=False,
                help="process forum posts (default)"),
            make_option('--comments',
                action='store_true',
                default=False,
                help="process comments"),
            make_option('--start',
                type='int',
                help="object to start at"),
            make_option('--end',
                type='int',
                help="one past the end object"),
            )

    def handle_noargs(self, **options):
        _setup_logging()

        do_comments = options['comments']
        do_forums = options['forums']
        if do_comments and do_forums:
            raise CommandError("Please specify --forums or --comments, not both")
        elif not do_comments and not do_forums:
            raise CommandError("Please specify --forums or --comments")

        logger.info("Arguments received: %s", options)
