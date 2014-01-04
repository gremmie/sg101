"""
Tasks for our custom search application.

"""
from __future__ import absolute_import

from celery import shared_task
from celery.utils.log import get_task_logger
from django.conf import settings

from queued_search.management.commands.process_search_queue import Command

logger = get_task_logger(__name__)


@shared_task
def process_search_queue_task():
    """
    Celery task to run the queued_search application's process_search_queue
    command.

    """
    if settings.SEARCH_QUEUE_ENABLED:
        command = Command()
        command.execute()
    else:
        logger.warning("Search queue disabled; skipping processing")
