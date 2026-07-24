"""oembed_refresh -
A custom management command to refresh the oEmbed HTML for the oEmbed objects in
our database.
This command is currently designed to fix up SSL mixed content issues. In the
future it would be nice to rework this command to refresh oEmbed objects if they
are older than some date.
"""
import datetime
import logging
import os.path
import re
from urllib.error import HTTPError, URLError

from django.core.management.base import BaseCommand
from django.conf import settings

from oembed.core import get_oembed
from oembed.models import Oembed
from oembed.models import Provider


LOGFILE = os.path.join(settings.PROJECT_PATH, 'logs', 'oembed_refresh.log')
logger = logging.getLogger(__name__)


def _setup_logging():
    logger.setLevel(logging.DEBUG)
    logger.propagate = False
    handler = logging.FileHandler(filename=LOGFILE, encoding='utf-8')
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)


def error_html(oembed):
    """Returns a string of HTML to be used when we can't retrieve the oEmbed
    data.
    """
    return u'<p>Video: <a href="{url}">{title}</a></p>'.format(
                url=oembed.url, title=oembed.title)


def refresh_html(providers, oembed):
    """Refresh the oEmbed HTML for the given oembed object."""

    # Find provider
    for p in providers:
        if re.match(p.url_regex, oembed.url):
            endpoint = p.api_endpoint
            break
    else:
        logger.error(u"No provider found for %s", oembed)
        return

    html = None
    try:
        result = get_oembed(endpoint, oembed.url, fmt='json',
                            maxwidth=settings.OEMBED_MAXWIDTH,
                            maxheight=settings.OEMBED_MAXHEIGHT,
                            scheme='https')
    except HTTPError as ex:
        if 400 <= ex.code < 500:
            logger.error(u"Server could not handle request for %s: %d", oembed, ex.code)
            html = error_html(oembed)
        else:
            logger.critical(u"Server error during request for %s: %d", oembed, ex.code)

    except URLError as ex:
        logger.critical(u"Failed to reach provider for %s: %s", oembed, ex.reason)
    else:
        html = result['html']

    if html:
        logger.info(u"Updating %s", oembed)
        oembed.html = html
        oembed.save()


class Command(BaseCommand):
    help = "Refresh oEmbed objects by requesting new data from providers"""

    def handle(self, *args, **options):
        time_started = datetime.datetime.now()
        _setup_logging()
        logger.info("Starting; arguments received: %s", options)

        providers = list(Provider.objects.all())

        qs = Oembed.objects.all()
        for oembed in qs.iterator():
            if 'https:' not in oembed.html:
                refresh_html(providers, oembed)

        time_finished = datetime.datetime.now()
        elapsed = time_finished - time_started
        logger.info("Finished; elapsed time: %s", elapsed)
